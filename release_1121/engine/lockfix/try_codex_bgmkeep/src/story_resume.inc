// Included inside LyricSave. All native slot handles used here are read-only.
namespace StoryResume {
using Bytes=std::vector<unsigned char>;
using Digest=std::array<unsigned char,32>;
struct Catalog {
    std::wstring folder;
    Digest scenario{},companion{};
    unsigned titleOwner=0,storyOwner=0;
    std::string tag;
    Bytes program;
    std::map<std::string,Digest> modules;
    std::map<std::string,std::set<std::string>> points;
};
static bool hash(const void* value,size_t length,Digest& out) {
    return length<=MAXDWORD && BCryptHash(BCRYPT_SHA256_ALG_HANDLE,nullptr,0,
        (PUCHAR)value,(ULONG)length,out.data(),(ULONG)out.size())>=0;
}
static bool localFile(const std::wstring& path,Bytes& bytes,DWORD limit) {
    HANDLE f=CreateFileW(path.c_str(),GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,0,nullptr);
    if(f==INVALID_HANDLE_VALUE)return false;
    bool ok=readBytes(f,bytes,limit);CloseHandle(f);return ok;
}
static bool sameFile(const std::wstring& path,const Digest& expected) {
    Bytes bytes;Digest got{};
    return localFile(path,bytes,256*1024*1024)&&hash(bytes.data(),bytes.size(),got)&&got==expected;
}
static bool stringField(Reader& r,std::string& text,unsigned limit) {
    unsigned n=0;if(!r.number(n)||!n||n>limit)return false;
    text.resize(n);
    return r.take(text.data(),n)&&text.find('\0')==std::string::npos;
}
static void trace(const char* stage){
    wchar_t path[32768];DWORD n=GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",path,_countof(path));
    if(!n||n>=_countof(path))return;
    std::wstring file=std::wstring(path,n)+L"\\story-resume.log";
    HANDLE h=CreateFileW(file.c_str(),FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,0,nullptr);
    if(h!=INVALID_HANDLE_VALUE){DWORD wrote=0;WriteFile(h,stage,(DWORD)strlen(stage),&wrote,nullptr);WriteFile(h,"\r\n",2,&wrote,nullptr);CloseHandle(h);}
}
static Catalog loadCatalog(const std::wstring& folder) {
    Bytes bytes;if(!localFile(folder+L"story-resume.n2r",bytes,40*1024*1024))return {};
    Catalog c;Reader r{bytes};char magic[8];unsigned size=0,n=0;Digest expected{},got{};
    if(!r.take(magic,8)||memcmp(magic,"N2SR03\0",8)||!r.take(c.scenario.data(),32)||!r.take(c.companion.data(),32)||
       !r.number(c.titleOwner)||!r.number(c.storyOwner)||c.titleOwner==c.storyOwner||!stringField(r,c.tag,64)||
       !r.take(expected.data(),32)||!r.number(size)||size<1024||size>32*1024*1024)return {};
    c.program.resize(size);
    if(!r.take(c.program.data(),size)||!hash(c.program.data(),size,got)||got!=expected||
       !r.number(n)||!n||n>4096)return {};
    for(unsigned i=0;i<n;++i){
        std::string key;Digest d{};
        if(!stringField(r,key,126)||!r.take(d.data(),32)||!c.modules.emplace(key,d).second)return {};
    }
    if(!r.number(n)||n>1024||!n)return {};
    for(unsigned i=0;i<n;++i){
        std::string scene;unsigned count=0;
        if(!stringField(r,scene,80)||!r.number(count)||!count||count>4096)return {};
        auto& points=c.points[scene];
        for(unsigned j=0;j<count;++j){std::string label;if(!stringField(r,label,48)||!points.insert(label).second)return {};}
    }
    if(r.offset!=bytes.size()||!sameFile(folder+L"..\\nss.npa",c.scenario)||!sameFile(folder+L"..\\krresume.npa",c.companion))return {};
    c.folder=folder;return c;
}
static unsigned u32(const char* p){unsigned n;memcpy(&n,p,4);return n;}
static bool variableIs(const std::string& vars,const char* name,bool active) {
    std::string key=std::string(name)+std::string(4,'\0');
    size_t p=vars.find(key);
    if(p==std::string::npos)return !active;
    if(!p||p+key.size()+8>vars.size())return false;
    unsigned type=(unsigned char)vars[p-1];double v=0;
    if(type==1)return false;
    if(type==2)memcpy(&v,vars.data()+p+key.size(),8);else if(type!=0)return false;
    return active?(v==1.0):(v==0.0);
}
static bool supported(const std::string& vars,const Catalog& c,std::string& scene,bool& choice) {
    scene=savedString(vars,"$GameName");
    auto found=c.points.find(scene);if(found==c.points.end())return false;
    if(!variableIs(vars,"$GameStart",true)||!variableIs(vars,"$GameCircle",true)||
       !variableIs(vars,"$PLACE_reco",false)||!variableIs(vars,"$PLACE_end",false)||
       !variableIs(vars,"$KR_REPLAY",false))return false;
    choice=found->second.count("choice")>0;
    if(choice)return true;
    auto label=savedString(vars,"$SYSTEM_present_text");
    if(label.size()<6||label.front()!='@')return false;
    label.erase(0,1);
    if(label[0]=='m'||label[0]=='n'||label[0]=='j')label.erase(0,1);
    return found->second.count(label)!=0;
}
static bool needsUpdate(const Bytes& file,const std::string& scene,const Catalog& c,const Patch* timing,size_t count) {
    std::string doc;
    if(!savePlain(file,"NPSS",doc)||doc.size()<16||u32(doc.data()+12)!=2||doc.find(c.tag)!=std::string::npos)return false;
    // Known byte-preserving lyric upgrades keep the native playback position in a current save.
    Bytes fixed=file;bool repaired=false;
    for(size_t i=0;i<count;++i)if(!timing[i].spans.empty())repaired=apply(fixed,timing[i])||repaired;
    if(repaired&&!savePlain(fixed,"NPSS",doc))return false;
    bool common=false,active=false,old=false;size_t pos=0;
    while((pos=doc.find("nss\\",pos))!=std::string::npos){
        size_t start=pos+4;pos=start;
        size_t z=doc.find('\0',start);
        if(z==std::string::npos||z-start>126||z+8>doc.size()||doc.compare(z,4,std::string(4,'\0')))continue;
        auto name=doc.substr(start,z-start);auto mod=c.modules.find(name);if(mod==c.modules.end())continue;
        unsigned len=u32(doc.data()+z+4);size_t at=z+8;
        if(!len||len>doc.size()-at)continue;
        if(name=="function.nss")common=true;
        if(name==scene)active=true;
        if(!old){
            std::string text=doc.substr(at,len);std::replace(text.begin(),text.end(),'\r','\n');Digest d{};
            if(!hash(text.data(),text.size(),d))return false;
            old=d!=mod->second;
        }
        pos=at+len;
    }
    return common&&active&&old;
}
static bool begins(const std::string& s,const char* prefix){return s.compare(0,strlen(prefix),prefix)==0;}
struct FrameRecord{size_t at;unsigned size,owner;std::string command;};
static bool rebuildFrames(Bytes& bytes,unsigned newTitle,unsigned newStory,bool choice,std::array<unsigned,2>* collect=nullptr) {
    std::string src;if(!savePlain(bytes,"NPSD",src)||src.size()<16)return false;
    unsigned count=u32(src.data()+12);if(!count||count>8192)return false;
    std::vector<FrameRecord> records;unsigned title=0,story=0;size_t pos=16;
    bool choiceUI=false;
    for(unsigned i=0;i<count;++i){
        if(src.size()-pos<4)return false;
        unsigned size=u32(src.data()+pos);pos+=4;
        if(size<13||size>src.size()-pos)return false;
        auto end=src.find('\0',pos+12);if(end==std::string::npos||end>=pos+size)return false;
        unsigned owner=u32(src.data()+pos);std::string cmd=src.substr(pos+12,end-pos-12);
        if(begins(cmd,"CreateSound(\"lx001\",BGM,")){if(title&&title!=owner)return false;title=owner;}
        if(cmd=="CreateName(\"StNameX\");"){if(story&&story!=owner)return false;story=owner;}
        if(begins(cmd,"CreateChoice("))choiceUI=true;
        records.push_back({pos,size,owner,std::move(cmd)});pos+=size;
    }
    if(pos!=src.size()||!title||!story||title==story)return false;
    if(collect){*collect={title,story};return true;}
    if(choice!=choiceUI)return false;
    std::string out=src.substr(0,16);unsigned kept=0;
    const std::string choiceName="\x91\x49\x91\xf0\x8e\x88"; // 選択肢 in CP932
    for(const auto& rec:records){
        if(rec.owner!=title&&rec.owner!=story)return false;
        auto& cmd=rec.command;
        if(!begins(cmd,"Create")&&!begins(cmd,"LoadImage(")){
            if(!cmd.empty()&&(unsigned char)cmd[0]!=0x11)return false;
            continue; // PRE or choice text is recreated from the current scenario.
        }
        if(begins(cmd,"CreateProcess(\"krJswap\"")||begins(cmd,"CreateProcess(\"krly_proc\"")||begins(cmd,"CreateTexture(\"krly_img"))continue;
        if(choice&&(begins(cmd,"CreateChoice(")||begins(cmd,"LoadImage(\"select_img")||
             cmd.substr(0,cmd.find(',')).find(choiceName)!=std::string::npos))continue;
        auto owner=rec.owner==title?newTitle:newStory;
        out.append((const char*)&rec.size,4);out.append((const char*)&owner,4);
        out.append(src,rec.at+4,rec.size-4);++kept;
    }
    unsigned size=(unsigned)out.size();
    memcpy(out.data()+8,&size,4);memcpy(out.data()+12,&kept,4);
    SaveEncoding enc(bytes[16]);bytes.resize(16+size);memcpy(bytes.data()+4,&size,4);memcpy(bytes.data()+8,&size,4);
    for(size_t i=0;i<size;++i)bytes[16+i]=enc.inverse[(unsigned char)out[i]];
    return true;
}
struct SlotStamp{
    std::array<unsigned long long,6> fields{};
    bool read(const std::string& folder){
        size_t i=0;
        for(auto name:{"script.npf","frames.npf","val.npf"}){
            WIN32_FILE_ATTRIBUTE_DATA f{};
            if(!GetFileAttributesExA((folder+name).c_str(),GetFileExInfoStandard,&f))return false;
            fields[i++]=((unsigned long long)f.ftLastWriteTime.dwHighDateTime<<32)|f.ftLastWriteTime.dwLowDateTime;
            fields[i++]=((unsigned long long)f.nFileSizeHigh<<32)|f.nFileSizeLow;
        }
        return true;
    }
};
static HANDLE temporary(const Bytes& bytes,const std::wstring& folder) {
    static std::atomic<unsigned> serial{0};
    for(unsigned i=0;i<12;++i){
        wchar_t leaf[80];swprintf_s(leaf,L"story-view-%lu-%u.tmp",GetCurrentProcessId(),++serial);
        HANDLE h=CreateFileW((folder+leaf).c_str(),GENERIC_READ|GENERIC_WRITE|DELETE,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
                     nullptr,CREATE_NEW,FILE_ATTRIBUTE_TEMPORARY|FILE_FLAG_DELETE_ON_CLOSE,nullptr);
        if(h==INVALID_HANDLE_VALUE){if(GetLastError()==ERROR_FILE_EXISTS)continue;return h;}
        DWORD n=0;
        if(WriteFile(h,bytes.data(),(DWORD)bytes.size(),&n,nullptr)&&n==bytes.size())return h;
        CloseHandle(h);break;
    }
    return INVALID_HANDLE_VALUE;
}
enum class Phase{Idle,Entering,Preparing,Ready,Restoring,Fallback,Bypass};
struct Pair {
    HANDLE program=INVALID_HANDLE_VALUE,frames=INVALID_HANDLE_VALUE;
    HANDLE currentProgram=INVALID_HANDLE_VALUE,currentFrames=INVALID_HANDLE_VALUE;
    std::string dir;std::wstring folder;SlotStamp stamp;Bytes originalFrames;
    bool choice=false;Phase phase=Phase::Idle;
    void clear(){
        for(auto h:{program,frames,currentProgram,currentFrames})if(h!=INVALID_HANDLE_VALUE)CloseHandle(h);
        program=frames=currentProgram=currentFrames=INVALID_HANDLE_VALUE;dir.clear();originalFrames.clear();phase=Phase::Idle;
    }
    ~Pair(){clear();}
};
static Pair& state(){static Pair p;return p;}
static std::mutex& stateLock(){static std::mutex m;return m;}
static void reset(){std::lock_guard<std::mutex> g(stateLock());state().clear();}
static bool queried(int id){
    std::lock_guard<std::mutex> g(stateLock());auto phase=state().phase;
    return id==-947021?phase==Phase::Entering:(phase==Phase::Ready||phase==Phase::Fallback);
}
static bool startCapture(){
    std::lock_guard<std::mutex> g(stateLock());auto& p=state();if(p.phase!=Phase::Entering)return false;
    p.phase=Phase::Preparing;return true;
}
static void finishCapture(Bytes& script,Bytes& currentObjects,bool success){
    std::lock_guard<std::mutex> g(stateLock());auto& p=state();if(p.phase!=Phase::Preparing)return;
    p.phase=Phase::Fallback;
    std::array<unsigned,2> owners{};std::string program;
    if(!success||!savePlain(script,"NPSS",program)||program.find(std::string("krresume")+char(92)+"r")==std::string::npos||
       !rebuildFrames(currentObjects,0,0,false,&owners))return;
    Bytes objects=p.originalFrames;
    if(!rebuildFrames(objects,owners[0],owners[1],p.choice))return;
    p.currentProgram=temporary(script,p.folder);p.currentFrames=temporary(objects,p.folder);
    if(p.currentProgram!=INVALID_HANDLE_VALUE&&p.currentFrames!=INVALID_HANDLE_VALUE)p.phase=Phase::Ready;
    trace(p.phase==Phase::Ready?"prepared original scene objects inside current scene":"could not prepare final scene objects");
}
static int startReload(){
    std::lock_guard<std::mutex> g(stateLock());auto& p=state();
    if((p.phase!=Phase::Ready&&p.phase!=Phase::Fallback)||p.dir.size()<5)return -1;
    p.phase=p.phase==Phase::Ready?Phase::Restoring:Phase::Bypass;
    return atoi(p.dir.substr(p.dir.size()-5,4).c_str());
}
static void finishReload(){
    std::lock_guard<std::mutex> g(stateLock());state().clear();
}
static HANDLE reopen(HANDLE h){
    if(h==INVALID_HANDLE_VALUE)return h;
    return ReOpenFile(h,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,0);
}
static HANDLE open(const char* path,bool wantProgram,const Patch& broken,const std::wstring& folder,const Patch* timing,size_t nTiming,const Bytes* request=nullptr) {
    try{
        std::string dir(path,strlen(path)-10);
        auto norm=dir;std::replace(norm.begin(),norm.end(),'/','\\');
        // The native jump journal owns its own captures and exact suspended frame.
        if(norm.size()<10||norm.compare(norm.size()-10,5,"1.00\\"))return INVALID_HANDLE_VALUE;
        static const Catalog cat=loadCatalog(folder);if(cat.folder.empty()){trace("no matching catalog");return INVALID_HANDLE_VALUE;}
        std::lock_guard<std::mutex> guard(stateLock());auto& pair=state();
        if(pair.dir==dir&&pair.phase==Phase::Bypass)return INVALID_HANDLE_VALUE;
        if(pair.dir==dir&&pair.phase==Phase::Restoring)return reopen(wantProgram?pair.currentProgram:pair.currentFrames);
        SlotStamp before;if(!before.read(dir)){trace("slot attributes unavailable");return INVALID_HANDLE_VALUE;}
        if(pair.dir==dir&&before.fields==pair.stamp.fields)return reopen(wantProgram?pair.program:pair.frames);
        pair.clear();pair.dir=dir;pair.stamp=before;
        Bytes values,program,frames;std::string vars,scene;bool choice=false;
        if(!readSibling(dir+"val.npf",values,32*1024*1024)||!savePlain(values,"NPSL",vars)||!supported(vars,cat,scene,choice)){trace("slot variables unsupported");return INVALID_HANDLE_VALUE;}
        if(wantProgram&&request)program=*request;
        else if(!readSibling(dir+"script.npf",program,64*1024*1024)){trace("saved program read failed");return INVALID_HANDLE_VALUE;}
        if(!needsUpdate(program,scene,cat,timing,nTiming)){trace("current or unsupported saved program");return INVALID_HANDLE_VALUE;}
        if(!wantProgram&&request)frames=*request;
        else if(!readSibling(dir+"frames.npf",frames,64*1024*1024)){trace("saved frames read failed");return INVALID_HANDLE_VALUE;}
        repairFrames(frames,(dir+"frames.npf").c_str(),broken,&program,&vars);
        pair.originalFrames=frames;pair.folder=folder;pair.choice=choice;
        if(!rebuildFrames(frames,cat.titleOwner,cat.storyOwner,choice)){trace("unsupported frame owner or type");return INVALID_HANDLE_VALUE;}
        SlotStamp after;if(!after.read(dir)||before.fields!=after.fields){pair.clear();return INVALID_HANDLE_VALUE;}
        pair.program=temporary(cat.program,folder);pair.frames=temporary(frames,folder);
        HANDLE p=reopen(pair.program),f=reopen(pair.frames);
        if(p==INVALID_HANDLE_VALUE||f==INVALID_HANDLE_VALUE){
            if(p!=INVALID_HANDLE_VALUE)CloseHandle(p);
            if(f!=INVALID_HANDLE_VALUE)CloseHandle(f);
            pair.clear();return INVALID_HANDLE_VALUE;
        }
        pair.phase=Phase::Entering;trace("prepared current story and original objects");if(wantProgram){CloseHandle(f);return p;}CloseHandle(p);return f;
    }catch(...){return INVALID_HANDLE_VALUE;}
}
} // namespace StoryResume
