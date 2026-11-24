// Backlog checkpoints use the native serializer/loader at script-safe Save/Load calls.
// Reserved negative IDs are an inert capability bridge when this DLL is absent.
// Content-addressed compressed chunks share immutable script/art/image data across points.
#include <cstdio>
#include <string>
#include <map>
#include <set>
#include <algorithm>
#include <compressapi.h>
#include <deque>
#include <fstream>
static void* origJumpSave;
static void* origJumpExists;
static void* origJumpLoad;
static void* origJumpClear;
extern "C" int __cdecl N2HD_BacklogPlacement(int*,int);
extern "C" void __cdecl N2HD_Trace(int);
namespace Jump {
const int Capture=-947001,Poll=-947002,Seal=-947003;
const size_t ChunkSize=65536,MaxFile=64*1024*1024;
struct File {std::string name;unsigned size;std::vector<std::string> chunks;};
struct Point {std::string id,parent;unsigned start=0,end=0;uint64_t prefix=0;bool sealed=false;std::vector<File> files;bool archived=true;};   // archived=false: files still being chunked by the archive thread
static std::vector<Point> points;
static std::string root,work,liveId;
static COMPRESSOR_HANDLE compressor=0;
static DECOMPRESSOR_HANDLE decompressor=0;
static int pending=-1,hover=-1,restores=0,errors=0;
static unsigned captured=0,polls=0,downs=0;
static bool loading=false,enabled=true,open=false,held=false,resetId=false;
static uint64_t rawBytes=0,storedBytes=0,lastCaptureMs=0;
static SRWLOCK lock=SRWLOCK_INIT;
struct Lock{Lock(){AcquireSRWLockExclusive(&lock);}~Lock(){ReleaseSRWLockExclusive(&lock);}};
static std::wstring wp(const std::string& p){int n=MultiByteToWideChar(CP_ACP,0,p.data(),(int)p.size(),0,0);std::wstring w(n,0);MultiByteToWideChar(CP_ACP,0,p.data(),(int)p.size(),&w[0],n);std::replace(w.begin(),w.end(),L'/',L'\\');return L"\\\\?\\"+w;}
__declspec(align(8)) static volatile LONG64 hoverRange=0;
static void setHoverRange(unsigned lo=0,unsigned hi=0){InterlockedExchange64(&hoverRange,((LONG64)hi<<32)|lo);}
static bool dir(const std::string& p){DWORD a=GetFileAttributesW(wp(p).c_str());if(a!=INVALID_FILE_ATTRIBUTES)return (a&FILE_ATTRIBUTE_DIRECTORY)&&!(a&FILE_ATTRIBUTE_REPARSE_POINT);return CreateDirectoryW(wp(p).c_str(),0)!=FALSE;}
static std::string hex(const void* bytes,size_t n){static const char* d="0123456789abcdef";std::string s;const unsigned char* p=(const unsigned char*)bytes;for(size_t i=0;i<n;++i){s+=d[p[i]>>4];s+=d[p[i]&15];}return s;}
static bool token(const std::string& s,size_t n){return s.size()==n&&s.find_first_not_of("0123456789abcdef")==std::string::npos;}
// Test timing (Claude 10-27): where a checkpoint capture spends its time.
static double jtSha,jtWrite,jtRead;static unsigned jtNew;
static double jtNow(){static LARGE_INTEGER f;LARGE_INTEGER c;if(!f.QuadPart)QueryPerformanceFrequency(&f);QueryPerformanceCounter(&c);return c.QuadPart*1000.0/f.QuadPart;}
static std::string sha(const unsigned char* p,size_t n){BCRYPT_ALG_HANDLE a=0;BCRYPT_HASH_HANDLE h=0;unsigned char b[32];bool ok=BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,0,0)>=0&&BCryptCreateHash(a,&h,0,0,0,0,0)>=0&&BCryptHashData(h,(PUCHAR)p,(ULONG)n,0)>=0&&BCryptFinishHash(h,b,32,0)>=0;if(h)BCryptDestroyHash(h);if(a)BCryptCloseAlgorithmProvider(a,0);return ok?hex(b,32):"";}
static bool read(const std::string& path,std::vector<unsigned char>& b,size_t max=MaxFile){HANDLE h=CreateFileW(wp(path).c_str(),GENERIC_READ,FILE_SHARE_READ,0,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,0);if(h==INVALID_HANDLE_VALUE)return false;BY_HANDLE_FILE_INFORMATION info={};LARGE_INTEGER n={};bool ok=GetFileInformationByHandle(h,&info)&&!(info.dwFileAttributes&FILE_ATTRIBUTE_REPARSE_POINT)&&GetFileSizeEx(h,&n)&&n.QuadPart>=0&&(uint64_t)n.QuadPart<=max;DWORD got=0;if(ok){b.resize((size_t)n.QuadPart);ok=b.empty()||ReadFile(h,b.data(),(DWORD)b.size(),&got,0)&&got==b.size();}CloseHandle(h);return ok;}
static bool write(const std::string& path,const std::vector<unsigned char>& b){std::string tmp=path+".tmp-"+std::to_string(GetCurrentProcessId());HANDLE h=CreateFileW(wp(tmp).c_str(),GENERIC_WRITE,0,0,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,0);if(h==INVALID_HANDLE_VALUE)return false;DWORD put=0;bool ok=WriteFile(h,b.data(),(DWORD)b.size(),&put,0)&&put==b.size()&&FlushFileBuffers(h);CloseHandle(h);if(ok)ok=MoveFileExW(wp(tmp).c_str(),wp(path).c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;if(!ok)DeleteFileW(wp(tmp).c_str());return ok;}
static unsigned char* var(const char* name){return ((unsigned char*(__cdecl*)(const char*))0x465130)(name);}
static std::string savedId(){auto v=var("$N2HD_BJ_ID");if(!v||v[0]!=1)return "";const char* s=(char*)v+0x98;size_t n=strnlen(s,64);return n==32&&token(std::string(s,n),32)?std::string(s,n):"";}
static void setId(const std::string& id){auto v=var("$N2HD_BJ_ID");if(v){v[0]=1;memset(v+0x98,0,1024);memcpy(v+0x98,id.data(),id.size());}}
static bool init(){
 if(!root.empty())return enabled;
 const char* base=(const char*)0x5a54b4;if(!base[0]||strlen(base)>170)return false;
 char exe[260];if(!GetModuleFileNameA(0,exe,260))return false;std::string nss=exe;nss=nss.substr(0,nss.find_last_of("\\/")+1)+"nss.npa";std::vector<unsigned char> b;if(!read(nss,b,128*1024*1024))return false;std::string h=sha(b.data(),b.size());if(h.size()!=64)return false;
 std::string parent=std::string(base)+"\\n2hd-jump-v1";
 if(!dir(parent))return false;root=parent+"\\"+h.substr(0,16);
 work=root+"\\work-"+std::to_string(GetCurrentProcessId());
 if(!dir(root)||!dir(root+"\\blocks")||!dir(root+"\\points")||!dir(root+"\\refs")||!dir(work)||!dir(work+"\\images")||!dir(work+"\\0001")||!dir(work+"\\common")||!CreateCompressor(COMPRESS_ALGORITHM_XPRESS_HUFF,0,&compressor)||!CreateDecompressor(COMPRESS_ALGORITHM_XPRESS_HUFF,0,&decompressor)){enabled=false;return false;}
 return true;
}
static std::vector<std::string> names(const std::string& folder,const char* pattern){std::vector<std::string> out;WIN32_FIND_DATAA f;HANDLE h=FindFirstFileA((folder+"\\"+pattern).c_str(),&f);if(h==INVALID_HANDLE_VALUE)return out;do{if(!(f.dwFileAttributes&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)))out.push_back(f.cFileName);}while(FindNextFileA(h,&f));FindClose(h);std::sort(out.begin(),out.end());return out;}
static void clearScratch(){for(auto sub:{"0001","images","common"})for(const auto& n:names(work+"\\"+sub,"*.npf"))DeleteFileA((work+"\\"+sub+"\\"+n).c_str());}
static bool safeName(const std::string& n){if(n=="0001\\script.npf"||n=="0001\\frames.npf"||n=="0001\\bklg.npf"||n=="0001\\val.npf")return true;if(n.size()!=20||n.compare(0,12,"images\\0001_")||n.substr(16)!=".npf")return false;return n.substr(12,4).find_first_not_of("0123456789")==std::string::npos;}
static void u32(std::vector<unsigned char>& b,unsigned n){for(int j=0;j<4;++j)b.push_back((unsigned char)(n>>(8*j)));}
static void str(std::vector<unsigned char>& b,const std::string& s){u32(b,(unsigned)s.size());b.insert(b.end(),s.begin(),s.end());}
static bool savePoint(const Point& p){std::vector<unsigned char>b;u32(b,0x314a424e);str(b,p.id);str(b,p.parent);u32(b,p.start);u32(b,p.end);u32(b,p.sealed?1:0);u32(b,(unsigned)p.prefix);u32(b,(unsigned)(p.prefix>>32));u32(b,(unsigned)p.files.size());for(const auto& f:p.files){str(b,f.name);u32(b,f.size);u32(b,(unsigned)f.chunks.size());for(const auto& h:f.chunks)str(b,h);}return write(root+"\\points\\"+p.id+".cpt",b);}
struct Reader{const std::vector<unsigned char>&b;size_t i=0;bool ok=true;unsigned n(){if(i+4>b.size()){ok=false;return 0;}unsigned v=0;for(int j=0;j<4;++j)v|=(unsigned)b[i++]<<(j*8);return v;}std::string s(unsigned max){unsigned z=n();if(!ok||z>max||i+z>b.size()){ok=false;return "";}std::string t((char*)b.data()+i,z);i+=z;return t;}};
static bool loadPoint(const std::string& id,Point& p){if(!token(id,32))return false;std::vector<unsigned char>b;if(!read(root+"\\points\\"+id+".cpt",b,1024*1024))return false;Reader r{b};if(r.n()!=0x314a424e)return false;p.id=r.s(32);p.parent=r.s(32);p.start=r.n();p.end=r.n();p.sealed=r.n()!=0;p.prefix=r.n();p.prefix|=(uint64_t)r.n()<<32;unsigned n=r.n();if(p.id!=id||(!p.parent.empty()&&!token(p.parent,32))||n>1000||p.start>0x200000||p.end>0x200000)return false;std::set<std::string> seen;for(unsigned i=0;i<n&&r.ok;++i){File f;f.name=r.s(64);f.size=r.n();unsigned c=r.n();if(!safeName(f.name)||!seen.insert(f.name).second||f.size>MaxFile||c!=(f.size+ChunkSize-1)/ChunkSize)return false;for(unsigned j=0;j<c&&r.ok;++j){auto h=r.s(64);if(!token(h,64))return false;f.chunks.push_back(h);}p.files.push_back(f);}return r.ok&&r.i==b.size()&&seen.count("0001\\script.npf")&&seen.count("0001\\frames.npf")&&seen.count("0001\\bklg.npf")&&seen.count("0001\\val.npf");}
static unsigned historySize(){auto b=*(unsigned char**)0x62993c;if(!b)return 0;auto start=(unsigned short*)(b+0x28),end=*(unsigned short**)(b+0x24);return end>=start&&end-start<=0x200000?(unsigned)(end-start):0;}
static int testJumpBack(){static int v=-2;if(v==-2){char b[16];v=GetEnvironmentVariableA("N2HD_TEST_JUMP_BACK",b,16)?atoi(b):-1;}return v;}
static void testLog(const char* line){char d[MAX_PATH];if(!GetEnvironmentVariableA("N2HD_PROFILE_DIR",d,MAX_PATH))return;char path[MAX_PATH];sprintf_s(path,"%s\\jumptest.log",d);FILE* f=0;if(!fopen_s(&f,path,"a")&&f){fprintf(f,"%llu %s\n",(unsigned long long)GetTickCount64(),line);fclose(f);}}
static uint64_t historyHash(unsigned count){auto b=*(unsigned char**)0x62993c;auto p=(unsigned short*)(b+0x28);uint64_t h=1469598103934665603ULL;for(unsigned i=0;i<count;++i)h=(h^p[i])*1099511628211ULL;return h;}
// Claude 10-27: new blocks are compressed and written by a worker thread. The capture runs on the script thread once
// per message and spent ~80 of its ~130 ms here (10-27 test: 38 new 64 KB blocks a message). The block hash is still
// taken here (the point lists its chunks); stage() and collect() wait for the queue before they read or delete blocks.
static SRWLOCK wLock=SRWLOCK_INIT;static CONDITION_VARIABLE wCv=CONDITION_VARIABLE_INIT,wIdle=CONDITION_VARIABLE_INIT;static bool wBusy,wStarted;
static std::deque<std::pair<std::string,std::vector<unsigned char>>> wQueue;static std::set<std::string> wKnown;
static void writeBlock(const std::string& path,const std::vector<unsigned char>& raw){SIZE_T need=0;Compress(compressor,raw.data(),raw.size(),0,0,&need);if(!need||need>ChunkSize*2){++errors;return;}
 std::vector<unsigned char> z(need);if(!Compress(compressor,raw.data(),raw.size(),z.data(),z.size(),&need)){++errors;return;}z.resize(need);
 std::vector<unsigned char>b;u32(b,0x314b4c42);u32(b,(unsigned)raw.size());b.insert(b.end(),z.begin(),z.end());if(!write(path,b)){++errors;return;}storedBytes+=b.size();}
static DWORD WINAPI writer(void*){for(;;){std::pair<std::string,std::vector<unsigned char>> job;AcquireSRWLockExclusive(&wLock);
  while(wQueue.empty()){wBusy=false;WakeAllConditionVariable(&wIdle);SleepConditionVariableSRW(&wCv,&wLock,INFINITE,0);}
  job=std::move(wQueue.front());wQueue.pop_front();wBusy=true;ReleaseSRWLockExclusive(&wLock);writeBlock(job.first,job.second);}}
static void drain(){if(!wStarted)return;AcquireSRWLockExclusive(&wLock);while(!wQueue.empty()||wBusy)SleepConditionVariableSRW(&wIdle,&wLock,INFINITE,0);ReleaseSRWLockExclusive(&wLock);}
static bool chunk(const unsigned char* p,size_t n,std::string& h){double t0=jtNow();h=sha(p,n);jtSha+=jtNow()-t0;if(h.size()!=64)return false;if(wKnown.count(h))return true;
 std::string path=root+"\\blocks\\"+h+".blk";wKnown.insert(h);if(GetFileAttributesW(wp(path).c_str())!=INVALID_FILE_ATTRIBUTES)return true;t0=jtNow();++jtNew;
 if(!wStarted){HANDLE th=CreateThread(0,0,writer,0,0,0);if(!th)return false;SetThreadPriority(th,THREAD_PRIORITY_BELOW_NORMAL);CloseHandle(th);wStarted=true;}
 AcquireSRWLockExclusive(&wLock);wQueue.emplace_back(path,std::vector<unsigned char>(p,p+n));wBusy=true;ReleaseSRWLockExclusive(&wLock);WakeConditionVariable(&wCv);jtWrite+=jtNow()-t0;return true;}
static bool archive(Point& cp){std::vector<std::string> files={"0001\\script.npf","0001\\frames.npf","0001\\bklg.npf","0001\\val.npf"};for(const auto& n:names(work+"\\images","0001_*.npf"))files.push_back("images\\"+n);for(const auto& n:files){if(!safeName(n))return false;std::vector<unsigned char>b;double tr=jtNow();if(!read(work+"\\"+n,b))return false;jtRead+=jtNow()-tr;File f{n,(unsigned)b.size(),{}};rawBytes+=b.size();for(size_t i=0;i<b.size();i+=ChunkSize){std::string h;if(!chunk(b.data()+i,std::min(ChunkSize,b.size()-i),h))return false;f.chunks.push_back(h);}cp.files.push_back(f);}return savePoint(cp);}
// Claude 10-27: the capture runs on the script thread once per message. Only the native save has to happen there; its
// files are moved to staging\<id> and this thread reads, hashes and chunks them, then writes the point (.cpt) and runs
// the periodic collect. Every capture had held its frame 90-190 ms (10-27 test, 18 of 18 captures).
struct ArchiveJob {std::string id,dir;std::vector<std::string> files;bool collect=false;};
static SRWLOCK aLock=SRWLOCK_INIT;static CONDITION_VARIABLE aCv=CONDITION_VARIABLE_INIT,aIdle=CONDITION_VARIABLE_INIT;static bool aBusy,aStarted;static std::deque<ArchiveJob> aQueue;
static void collect();
static void archiveJob(const ArchiveJob& j){
 if(j.collect){collect();return;}
 std::vector<File> files;bool ok=true;
 for(const auto& n:j.files){std::vector<unsigned char>b;if(!safeName(n)||!read(j.dir+"\\"+n,b)){ok=false;break;}File f{n,(unsigned)b.size(),{}};rawBytes+=b.size();
  for(size_t i=0;i<b.size();i+=ChunkSize){std::string h;if(!chunk(b.data()+i,std::min(ChunkSize,b.size()-i),h)){ok=false;break;}f.chunks.push_back(h);}if(!ok)break;files.push_back(f);}
 for(const auto& n:j.files)DeleteFileW(wp(j.dir+"\\"+n).c_str());RemoveDirectoryW(wp(j.dir+"\\0001").c_str());RemoveDirectoryW(wp(j.dir+"\\images").c_str());RemoveDirectoryW(wp(j.dir).c_str());
 Lock guard;for(auto& p:points)if(p.id==j.id){if(!ok){++errors;break;}p.files=files;p.archived=true;if(!savePoint(p))++errors;break;}}
static DWORD WINAPI archiver(void*){for(;;){ArchiveJob job;AcquireSRWLockExclusive(&aLock);
  while(aQueue.empty()){aBusy=false;WakeAllConditionVariable(&aIdle);SleepConditionVariableSRW(&aCv,&aLock,INFINITE,0);}
  job=std::move(aQueue.front());aQueue.pop_front();aBusy=true;ReleaseSRWLockExclusive(&aLock);archiveJob(job);}}
static bool enqueueArchive(ArchiveJob job){if(!aStarted){HANDLE th=CreateThread(0,0,archiver,0,0,0);if(!th)return false;SetThreadPriority(th,THREAD_PRIORITY_BELOW_NORMAL);CloseHandle(th);aStarted=true;}
 AcquireSRWLockExclusive(&aLock);aQueue.push_back(std::move(job));aBusy=true;ReleaseSRWLockExclusive(&aLock);WakeConditionVariable(&aCv);return true;}
// Before reading points or blocks: the archive thread first (it queues block writes), then the block writer.
static void drainAll(){N2HD_Trace(116);struct DrainEnd{~DrainEnd(){N2HD_Trace(117);}}drainEnd;if(aStarted){AcquireSRWLockExclusive(&aLock);while(!aQueue.empty()||aBusy)SleepConditionVariableSRW(&aIdle,&aLock,INFINITE,0);ReleaseSRWLockExclusive(&aLock);}drain();}
static bool expand(const File& f,std::vector<unsigned char>& out){out.clear();for(const auto& h:f.chunks){std::vector<unsigned char>b;if(!read(root+"\\blocks\\"+h+".blk",b,ChunkSize*2)||b.size()<9)return false;Reader r{b};if(r.n()!=0x314b4c42)return false;unsigned n=r.n();if(n<1||n>ChunkSize)return false;std::vector<unsigned char> raw(n);SIZE_T got=0;if(!Decompress(decompressor,b.data()+8,b.size()-8,raw.data(),n,&got)||got!=n||sha(raw.data(),raw.size())!=h)return false;out.insert(out.end(),raw.begin(),raw.end());}return out.size()==f.size;}
static bool stage(const Point& cp){drainAll();clearScratch();for(const auto& f:cp.files){std::vector<unsigned char>b;if(!expand(f,b)||!write(work+"\\"+f.name,b))return false;}return true;}
static void head(){std::vector<unsigned char>b(liveId.begin(),liveId.end());write(root+"\\refs\\live-"+std::to_string(GetCurrentProcessId())+".ref",b);}
// Collect only our namespace, keeping chains referenced by native saves and live game processes.
// Corrupt/unknown references abort collection conservatively.
static void collect(){
 drain();wKnown.clear();   // blocks may be deleted below; let chunk() look on disk again
 std::set<std::string> keepPoints,keepBlocks;
 for(const auto& name:names(root+"\\refs","*.ref")){
  if(name.compare(0,5,"live-")==0){
   unsigned pid=0;if(sscanf_s(name.c_str(),"live-%u.ref",&pid)!=1)continue;
   HANDLE h=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,pid);bool dead=false;
   if(h){DWORD code=STILL_ACTIVE;if(GetExitCodeProcess(h,&code)&&code!=STILL_ACTIVE)dead=true;CloseHandle(h);}
   else if(GetLastError()==ERROR_INVALID_PARAMETER)dead=true;
   if(dead){DeleteFileW(wp(root+"\\refs\\"+name).c_str());continue;}
  }else if(name.compare(0,5,"slot-")!=0)continue;
  std::vector<unsigned char>b;if(!read(root+"\\refs\\"+name,b,64))return;
  std::string id(b.begin(),b.end());if(id.empty())continue;if(!token(id,32))return;
  unsigned steps=0;
  while(!id.empty()&&keepPoints.insert(id).second){
   if(++steps>8192)return;Point p;if(!loadPoint(id,p))return;
   for(const auto& f:p.files)for(const auto& h:f.chunks)keepBlocks.insert(h);
   id=p.parent;
  }
 }
 for(const auto& n:names(root+"\\points","*.cpt"))if(n.size()==36&&token(n.substr(0,32),32)&&!keepPoints.count(n.substr(0,32)))DeleteFileW(wp(root+"\\points\\"+n).c_str());
 for(const auto& n:names(root+"\\blocks","*.blk"))if(n.size()==68&&token(n.substr(0,64),64)&&!keepBlocks.count(n.substr(0,64)))DeleteFileW(wp(root+"\\blocks\\"+n).c_str());
}
static void chain(const std::string& id){points.clear();pending=hover=-1;open=false;liveId="";std::set<std::string> seen;std::string cur=id;while(!cur.empty()&&points.size()<8192){if(!seen.insert(cur).second)break;Point p;if(!loadPoint(cur,p))break;points.push_back(p);cur=p.parent;}std::reverse(points.begin(),points.end());unsigned n=historySize();std::vector<uint64_t> hashes(n+1);hashes[0]=1469598103934665603ULL;auto history=(unsigned short*)(*(unsigned char**)0x62993c+0x28);for(unsigned j=0;j<n;++j)hashes[j+1]=(hashes[j]^history[j])*1099511628211ULL;for(auto i=points.begin();i!=points.end();){if(i->start>n||hashes[i->start]!=i->prefix)i=points.erase(i);else ++i;}if(!points.empty()){liveId=points.back().id;open=!points.back().sealed;}head();}
static int nativeSave(int id){int result;__asm{
 mov eax,id
 call dword ptr [origJumpSave]
 mov result,eax
 }return result;}
static int captureImpl();
static int capture(){int r=captureImpl();char l[80];sprintf_s(l,"capture hist=%u points=%u",historySize(),(unsigned)points.size());testLog(l);return r;}
static int captureImpl(){N2HD_Trace(110);struct TraceEnd{~TraceEnd(){N2HD_Trace(113);}}traceEnd;Lock guard;uint64_t t=GetTickCount64();if(!init())return 0;unsigned n=historySize();if(!points.empty()&&(n<points.back().start||historyHash(points.back().start)!=points.back().prefix)){points.clear();liveId="";}if(open&&!points.empty()){points.back().end=n;points.back().sealed=true;if(points.back().archived)savePoint(points.back());open=false;}
 Point cp;GUID g;if(FAILED(CoCreateGuid(&g)))return 0;cp.id=hex(&g,sizeof(g));cp.parent=liveId;cp.start=n;cp.prefix=historyHash(n);std::string oldId=savedId();setId(cp.id);resetId=false;double jt0=jtNow();clearScratch();double jt1=jtNow();char old[260];strcpy_s(old,(char*)0x5a54b4);strcpy_s((char*)0x5a54b4,260,work.c_str());unsigned char* tsv=GetEnvironmentVariableA("N2HD_TEST_SAVE_SKIP",0,0)?var("$SYSTEM_skip"):0;double tso=tsv?*(double*)(tsv+0x10):0;if(tsv)*(double*)(tsv+0x10)=1.0;   // test: checkpoints taken while skipping
 // Checkpoints are taken with skip, auto and the express skip off (put back right after): the save keeps the skip
 // state, and a jump to a point taken while skipping skipped on through the read text to the first unread line
 // (user, 10-27; turning the variables off after the load did not stop it).
 static const char* const quietVars[]={"$SYSTEM_skip","$SYSTEM_text_auto","#SYSTEM_skip_express","$LOCAL_sys_skip","$LOCAL_sys_auto","$LOCAL_skip"};
 double quietOld[6]={};unsigned char* quietPtr[6]={};bool quiet=!GetEnvironmentVariableA("N2HD_TEST_NO_JUMP_FIX",0,0);
 if(quiet)for(int i=0;i<6;++i){quietPtr[i]=var(quietVars[i]);if(quietPtr[i]){quietOld[i]=*(double*)(quietPtr[i]+0x10);*(double*)(quietPtr[i]+0x10)=0.0;}}
 int ok=nativeSave(1);
 if(quiet)for(int i=0;i<6;++i)if(quietPtr[i])*(double*)(quietPtr[i]+0x10)=quietOld[i];
 if(tsv)*(double*)(tsv+0x10)=tso;N2HD_Trace(111);strcpy_s((char*)0x5a54b4,260,old);double jt2=jtNow();jtSha=jtWrite=jtRead=0;jtNew=0;
 bool staged=false;
 if(ok){std::vector<std::string> files={"0001\\script.npf","0001\\frames.npf","0001\\bklg.npf","0001\\val.npf"};for(const auto& f:names(work+"\\images","0001_*.npf"))files.push_back("images\\"+f);
  std::string sd=root+"\\staging\\"+cp.id;staged=dir(root+"\\staging")&&dir(sd)&&dir(sd+"\\0001")&&dir(sd+"\\images");double tr=jtNow();
  for(const auto& f:files)if(staged&&!MoveFileExW(wp(work+"\\"+f).c_str(),wp(sd+"\\"+f).c_str(),MOVEFILE_REPLACE_EXISTING))staged=false;jtRead+=jtNow()-tr;
  if(staged){cp.archived=false;ArchiveJob job;job.id=cp.id;job.dir=sd;job.files=files;staged=enqueueArchive(std::move(job));}}
 if(staged){N2HD_Trace(112);points.push_back(cp);liveId=cp.id;open=true;++captured;head();if(captured==1||captured%64==0){ArchiveJob c;c.collect=true;enqueueArchive(std::move(c));}}else{setId(oldId);++errors;ok=0;}double jt5=jtNow();clearScratch();lastCaptureMs=GetTickCount64()-t;
 {char d[MAX_PATH];if(GetEnvironmentVariableA("N2HD_PROFILE_DIR",d,MAX_PATH)){char path[MAX_PATH];sprintf_s(path,"%s\\jump.log",d);FILE* f=0;if(!fopen_s(&f,path,"a")&&f){fprintf(f,"capture at=%.0f total=%.0f clear=%.0f save=%.0f read=%.0f sha=%.0f write=%.0f new=%u archive+collect=%.0f clear2=%.0f raw=%llu\n",jt0,jtNow()-jt0,jt1-jt0,jt2-jt1,jtRead,jtSha,jtWrite,jtNew,jt5-jt2,jtNow()-jt5,(unsigned long long)rawBytes);fclose(f);}}}
 return ok;
}
static int seal(){Lock guard;if(!points.empty()&&open){auto& p=points.back();p.end=historySize();p.sealed=true;open=false;if(p.archived&&!savePoint(p))++errors;}return 1;}
static bool range(int index,unsigned& lo,unsigned& hi){if(index<0||index>=(int)points.size())return false;const auto& p=points[index];lo=p.start;hi=p.sealed?p.end:historySize();return hi>lo&&hi<=historySize()&&historyHash(lo)==p.prefix;}
static int hit(){int x=0,y=0;((void(__cdecl*)(HWND,int*,int*))0x46b620)(*(HWND*)0x629854,&x,&y);if(x<78||x>920||y<48||y>524)return -1;int a[6000];int n=N2HD_BacklogPlacement(a,1000);auto base=*(unsigned char**)0x62993c;uintptr_t first=(uintptr_t)(base+0x28);int candidate=-1;for(int j=0;j<std::min(n,1000);++j){int* v=a+j*6;if(y<v[4]-10||y>v[4]+27||x<v[3]-3||x>v[3]+v[5]+4)continue;unsigned off=(unsigned)(((uintptr_t)(unsigned)v[0]-first)/2);auto it=std::upper_bound(points.begin(),points.end(),off,[](unsigned off,const Point& p){return off<p.start;});if(it!=points.begin()){int k=(int)(it-points.begin()-1);unsigned lo,hi;if(range(k,lo,hi)&&off>=lo&&off<hi)candidate=k;}if(candidate>=0)break;}return candidate;}
static void invalidate(){auto b=*(unsigned char**)0x62993c;if(b)*(int*)(b+4)=1;((void(__cdecl*)())0x44abc0)();((void(__cdecl*)(int,int))0x48f1a0)(1024,576);((void(__cdecl*)())0x44ac00)();}
static int poll(){++polls;if(!init())return 0;auto b=*(unsigned char**)0x62993c;if(!b||!*(int*)(b+8))return 0;int h=hit();bool changed=h!=hover;hover=h;unsigned lo=0,hi=0;if(range(h,lo,hi))setHoverRange(lo,hi);else setHoverRange();if(changed)invalidate();auto v=var("$SYSTEM_l_button_down");bool down=v&&*(double*)(v+0x10)!=0.0;
 if(!down){held=false;return 0;}++downs;if(testJumpBack()>0&&!held&&(int)points.size()>testJumpBack())h=(int)points.size()-1-testJumpBack();if(held||h<0)return 0;held=true;{char l[200];sprintf_s(l,"click point=%d of %u start=%u end=%u sealed=%d hist=%u",h,(unsigned)points.size(),points[h].start,points[h].end,points[h].sealed?1:0,historySize());testLog(l);}
 if(stage(points[h])){pending=h;*(double*)(v+0x10)=0;return 1;}++errors;return 0;
}
// Claude 11-24: J/K language switch mid-line ("해당 구역 로딩된건 바뀌지 않네"). Script ExistSave(-947004) stages the newest
// checkpoint (taken at this line's TypeBegin) and the script then Load(-947002)s it like a backlog jump: the line starts
// over and TypeBegin (sound_seek/jp_swap.py KrJBegin) types it in the new language. Auto/skip are left as they were.
static bool restartLoad=false;
static int restart(){if(!init()||points.empty())return 0;int h=(int)points.size()-1;
 {char l[120];sprintf_s(l,"restart point=%d of %u start=%u hist=%u",h,(unsigned)points.size(),points[h].start,historySize());testLog(l);}
 if(stage(points[h])){pending=h;restartLoad=true;bgmKeepSelect();return 1;}++errors;return 0;}
static int load(){LARGE_INTEGER lq0,lq1,lq2,lq3,lqf;QueryPerformanceFrequency(&lqf);QueryPerformanceCounter(&lq0);drainAll();QueryPerformanceCounter(&lq1);bool isJump=*(int*)0x5b3ec4==Poll;char old[260]={};loading=true;int selected=pending;
 if(isJump){if(selected<0||selected>=(int)points.size()){++errors;loading=false;return 0;}strcpy_s(old,(char*)0x5a54b4);strcpy_s((char*)0x5a54b4,260,work.c_str());*(int*)0x5b3ec4=1;}
 {char l[120];sprintf_s(l,"load jump=%d selected=%d hist_before=%u",isJump?1:0,selected,historySize());testLog(l);}int ok=((int(__cdecl*)())origJumpLoad)();QueryPerformanceCounter(&lq2);{char l[120];sprintf_s(l,"loaded ok=%d hist_after=%u",ok,historySize());testLog(l);}
 if(isJump)strcpy_s((char*)0x5a54b4,260,old);loading=false;
 // A checkpoint keeps $SYSTEM_skip / $SYSTEM_text_auto as they were when it was taken; a jump restored them and the
 // game skipped through the read text back to where the reader had been (user, 10-27). After a jump both are off.
// Codex 10-28: also apply the native SYSTEM-variable dispatcher, as val.npf loading does (0x46621c).
// Updating the stored double alone leaves the engine skip/auto state active; ECX is the variable name at +0x18.
 bool wasRestart=restartLoad;restartLoad=false;
 bgmKeepAfterLoad(ok&&wasRestart);   // Claude 11-24: J/K restart keeps the music (bgm_keep.inc)
 if(ok&&isJump&&!wasRestart&&!GetEnvironmentVariableA("N2HD_TEST_NO_JUMP_FIX",0,0))for(const char* n:{"$SYSTEM_skip","$SYSTEM_text_auto"}){auto v=var(n);if(!v)continue;{char l[120];sprintf_s(l,"jump off %s type=%d value=%g",n,v[0],*(double*)(v+0x10));testLog(l);}*(double*)(v+0x10)=0.0;((int(__thiscall*)(const char*))0x480cb0)((const char*)v+0x18);}
 if(ok){if(isJump)++restores;if(init())chain(savedId());}else ++errors;QueryPerformanceCounter(&lq3);
 {char l[160];sprintf_s(l,"load ms drain=%.0f engine=%.0f chain=%.0f",(lq1.QuadPart-lq0.QuadPart)*1000.0/lqf.QuadPart,(lq2.QuadPart-lq1.QuadPart)*1000.0/lqf.QuadPart,(lq3.QuadPart-lq2.QuadPart)*1000.0/lqf.QuadPart);testLog(l);}
 pending=hover=-1;setHoverRange();held=true;return ok;
}
static void saveReference(int slot,int ok){if(ok&&slot>0&&init()){drainAll();std::string id=savedId();std::vector<unsigned char>b(id.begin(),id.end());write(root+"\\refs\\slot-"+std::to_string(slot)+".ref",b);}}
}
// Scenario viewer playback (kr_scenario.nss sets $KR_REPLAY): no checkpoints and no backlog jumps, which would load the
// story state and leave the viewer.
static bool replaying(){auto v=Jump::var("$KR_REPLAY");return v&&*(double*)(v+0x10)!=0.0;}
static int __cdecl jumpCapture(){bgmKeepClear();static int off=-1;if(off<0)off=GetEnvironmentVariableA("N2HD_TEST_NO_JUMP",0,0)?1:0;if(off||replaying())return 1;return Jump::capture();}   // test switch: no checkpoints
static int __cdecl jumpSeal(){if(replaying())return 1;return Jump::seal();}
static int __cdecl jumpPoll(){if(replaying())return 0;return Jump::poll();}
static int __cdecl storyCheckpointQuery(int);
static int __cdecl storyCheckpointSave();
static int __cdecl storyCheckpointLoad();
static void __cdecl storyNormalLoadStart();
static int __cdecl jumpLoad(){
 int id=*(int*)0x5b3ec4;
 if(id==-947022)return storyCheckpointLoad();
 if(id!=Jump::Poll)storyNormalLoadStart();
 return Jump::load();
}
static int __cdecl jumpRestart(){if(replaying())return 0;return Jump::restart();}
static int __cdecl jumpNormalSave(int id){if(id==-947021)return storyCheckpointSave();N2HD_Trace(114);struct SaveEnd{~SaveEnd(){N2HD_Trace(115);}}saveEnd;if(Jump::resetId){Jump::setId("");Jump::resetId=false;}int r=Jump::nativeSave(id);Jump::saveReference(id,r);return r;}
static unsigned __cdecl jumpClear(){unsigned r=((unsigned(__cdecl*)())origJumpClear)();if(!Jump::loading){Jump::Lock guard;Jump::points.clear();Jump::liveId="";Jump::resetId=true;Jump::pending=Jump::hover=-1;Jump::setHoverRange();Jump::open=false;if(!Jump::root.empty())Jump::head();}return r;}
__declspec(naked) static void hookJumpSave(){__asm{
 cmp eax,-947001
 je capture
 cmp eax,-947003
 je seal
 push eax
 call jumpNormalSave
 add esp,4
 ret
capture:
 pushfd
 pushad
 call jumpCapture
 mov [esp+28],eax
 popad
 popfd
 ret
seal:
 pushfd
 pushad
 call jumpSeal
 mov [esp+28],eax
 popad
 popfd
 ret
}}
__declspec(naked) static void hookJumpExists(){__asm{
 cmp esi,-947021
 je storyquery
 cmp esi,-947022
 je storyquery
 cmp esi,-947001
 je available
 cmp esi,-947004
 je jrestart
 cmp esi,-947002
 jne original
 pushfd
 pushad
 call jumpPoll
 mov [esp+28],eax
 popad
 popfd
 ret
available:
 mov eax,1
 ret
storyquery:
 pushfd
 pushad
 push esi
 call storyCheckpointQuery
 add esp,4
 mov [esp+28],eax
 popad
 popfd
 ret
jrestart:
 pushfd
 pushad
 call jumpRestart
 mov [esp+28],eax
 popad
 popfd
 ret
original:
 jmp dword ptr [origJumpExists]
}}
extern "C" __declspec(dllexport) int __cdecl N2HD_JumpHover(unsigned* a,unsigned* b){uint64_t v=(uint64_t)InterlockedCompareExchange64(&Jump::hoverRange,0,0);*a=(unsigned)v;*b=(unsigned)(v>>32);return *b>*a;}
extern "C" __declspec(dllexport) void __cdecl N2HD_JumpStats(int* out){memset(out,0,144);out[0]=(int)Jump::points.size();out[1]=Jump::pending;out[2]=Jump::restores;out[3]=Jump::errors;out[4]=Jump::hover;out[5]=(int)Jump::captured;out[6]=(int)Jump::lastCaptureMs;out[7]=(int)Jump::rawBytes;out[8]=(int)Jump::storedBytes;out[9]=(int)Jump::polls;out[34]=(int)Jump::downs;out[35]=Jump::held?1:0;for(int i=0;i<(int)Jump::points.size()&&i<12;++i){out[10+i*2]=Jump::points[i].start;out[11+i*2]=Jump::points[i].sealed?Jump::points[i].end:-1;}}
