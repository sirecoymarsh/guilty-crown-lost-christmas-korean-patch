// Read-only compatibility view for native saves which contain the older common scenario script.
#include <algorithm>
#include <atomic>
#include <array>
#include <cwchar>

namespace LyricSave {
struct Span { unsigned offset; std::vector<unsigned char> bytes; };
struct Patch {
    std::vector<unsigned char> anchor;
    std::array<unsigned char,32> sha{};
    unsigned moduleSize=0;
    std::vector<Span> spans;
    std::wstring folder;
};
struct Reader {
    const std::vector<unsigned char>& data; size_t offset=0;
    bool take(void* dest,size_t count) {
        if(count>data.size()-offset)return false;
        memcpy(dest,data.data()+offset,count);offset+=count;return true;
    }
    bool number(unsigned& n){return take(&n,sizeof n);}
};
static bool readBytes(HANDLE file,std::vector<unsigned char>& dest,DWORD limit) {
    LARGE_INTEGER size{};if(!GetFileSizeEx(file,&size)||size.QuadPart<=0||size.QuadPart>limit)return false;
    dest.resize((size_t)size.QuadPart);DWORD got=0;
    return ReadFile(file,dest.data(),(DWORD)dest.size(),&got,nullptr)&&got==dest.size();
}
static Patch load(const wchar_t* name) {
    wchar_t exe[32768];DWORD len=GetModuleFileNameW(nullptr,exe,_countof(exe));
    if(!len||len>=_countof(exe))return {};
    std::wstring folder(exe,len);auto sep=folder.find_last_of(L"\\/");
    if(sep==std::wstring::npos)return {};
    folder.resize(sep+1);folder+=L"lyrics-resume\\";
    HANDLE file=CreateFileW((folder+name).c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(file==INVALID_HANDLE_VALUE)return {};
    std::vector<unsigned char> data;bool read=readBytes(file,data,1024*1024);CloseHandle(file);
    if(!read)return {};
    Reader in{data};char magic[8];unsigned an=0,nspans=0;
    Patch patch;patch.folder=folder;
    if(!in.take(magic,8)||memcmp(magic,"N2LYR01",8)||!in.number(patch.moduleSize)||patch.moduleSize<256||
       patch.moduleSize>2*1024*1024||!in.number(an)||!an||an>128||!in.number(nspans)||!nspans||nspans>256||
       !in.take(patch.sha.data(),patch.sha.size()))return {};
    patch.anchor.resize(an);if(!in.take(patch.anchor.data(),an))return {};
    unsigned lastEnd=0;
    for(unsigned i=0;i<nspans;++i) {
        unsigned off,n;if(!in.number(off)||!in.number(n)||!n||off<lastEnd||off>patch.moduleSize||n>patch.moduleSize-off)return {};
        Span span{off,std::vector<unsigned char>(n)};if(!in.take(span.bytes.data(),n))return {};
        lastEnd=off+n;patch.spans.push_back(std::move(span));
    }
    if(in.offset!=data.size())return {};
    return patch;
}
static bool matches(const unsigned char* data,const Patch& patch) {
    unsigned char digest[32];
    // BCryptHash's SHA-256 pseudo-handle is supported on the Windows versions used by the renderer.
    return BCryptHash(BCRYPT_SHA256_ALG_HANDLE,nullptr,0,const_cast<PUCHAR>(data),patch.moduleSize,digest,sizeof digest)>=0&&
           memcmp(digest,patch.sha.data(),sizeof digest)==0;
}
static bool apply(std::vector<unsigned char>& data,const Patch& patch) {
    if(data.size()<16||memcmp(data.data(),"NPSF",4))return false;
    uint32_t rawSize,stored,flags;memcpy(&rawSize,data.data()+4,4);memcpy(&stored,data.data()+8,4);memcpy(&flags,data.data()+12,4);
    if(flags||rawSize!=stored||rawSize!=data.size()-16)return false;
    auto p=data.begin()+16;bool changed=false;
    for(;;) {
        p=std::search(p,data.end(),patch.anchor.begin(),patch.anchor.end());
        if(p==data.end())break;
        p+=patch.anchor.size();
        if((size_t)(data.end()-p)<patch.moduleSize)break;
        if(!matches(&*p,patch))continue;
        for(const auto& span:patch.spans)std::copy(span.bytes.begin(),span.bytes.end(),p+span.offset);
        changed=true;p+=patch.moduleSize;
    }
    return changed;
}
#include "bgm_recovery.inc"
static bool isSlotFile(const char* name,const char* leaf) {
    if(!name)return false;size_t n=strlen(name);if(n<15||_stricmp(name+n-10,leaf))return false;
    auto slash=[](char c){return c=='\\'||c=='/';};
    if(!slash(name[n-11]))return false;
    for(size_t i=n-15;i<n-11;++i)if(name[i]<'0'||name[i]>'9')return false;
    return n==15||slash(name[n-16]);
}
static HANDLE WINAPI view(const char* name,DWORD access,DWORD share,LPSECURITY_ATTRIBUTES sa,DWORD disp,DWORD flags,HANDLE tmpl) {
    HANDLE original=CreateFileA(name,access,share,sa,disp,flags,tmpl);
    if(original==INVALID_HANDLE_VALUE||disp!=OPEN_EXISTING||(access&(GENERIC_WRITE|DELETE))||
       !(access&GENERIC_READ)||(flags&FILE_FLAG_OVERLAPPED))return original;
    bool script=isSlotFile(name,"script.npf"),frames=isSlotFile(name,"frames.npf");
    if(!script&&!frames)return original;
    static const Patch patch=load(L"data.n2l"),loops=load(L"loop.n2l");
    static const Patch broken=load(L"repair-v1.n2l"),oldLoops=load(L"repair-loop-v1.n2l");
    if(patch.spans.empty())return original;
    std::vector<unsigned char> data;
    bool ok=readBytes(original,data,64*1024*1024);
    LARGE_INTEGER zero{};SetFilePointerEx(original,zero,nullptr,FILE_BEGIN);
    if(!ok)return original;
    if(script){
        bool changed=apply(data,patch);
        if(!broken.spans.empty())changed=apply(data,broken)||changed;
        if(!changed)return original;
        if(!loops.spans.empty())apply(data,loops);
        if(!oldLoops.spans.empty())apply(data,oldLoops);
    }else if(!repairFrames(data,name,broken))return original;
    static std::atomic<unsigned> sequence{0};HANDLE temp=INVALID_HANDLE_VALUE;
    for(unsigned i=0;i<12&&temp==INVALID_HANDLE_VALUE;++i) {
        wchar_t leaf[64];swprintf_s(leaf,L"view-%lu-%u.tmp",GetCurrentProcessId(),++sequence);
        temp=CreateFileW((patch.folder+leaf).c_str(),GENERIC_READ|GENERIC_WRITE|DELETE,FILE_SHARE_READ|FILE_SHARE_DELETE,
                         nullptr,CREATE_NEW,FILE_ATTRIBUTE_TEMPORARY|FILE_FLAG_DELETE_ON_CLOSE,nullptr);
        if(temp==INVALID_HANDLE_VALUE&&GetLastError()!=ERROR_FILE_EXISTS)break;
    }
    if(temp==INVALID_HANDLE_VALUE)return original;
    DWORD put=0;if(!WriteFile(temp,data.data(),(DWORD)data.size(),&put,nullptr)||put!=data.size()||
                   !SetFilePointerEx(temp,zero,nullptr,FILE_BEGIN)){CloseHandle(temp);return original;}
    CloseHandle(original);return temp;
}
} // namespace LyricSave

