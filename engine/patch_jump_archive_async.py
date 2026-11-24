"""대사 기록 점프: 지점 저장 때 엔진 저장(대본 스레드에서만 가능)만 하고, 그 파일을 staging\\<id> 로 옮긴 뒤
읽기·해시·조각 쓰기·지점 기록(.cpt)·정리(collect)는 보관 스레드가 한다. 조각을 읽는 stage·load·saveReference 는 먼저 기다린다.
한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\backlog_jump.inc'); s = p.read_text('utf-8')


def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (old[:80], s.count(old))
    s = s.replace(old, new)


# 1) 지점: 보관이 끝났는지
rep('struct Point {std::string id,parent;unsigned start=0,end=0;uint64_t prefix=0;bool sealed=false;std::vector<File> files;};',
    'struct Point {std::string id,parent;unsigned start=0,end=0;uint64_t prefix=0;bool sealed=false;std::vector<File> files;bool archived=true;};   // archived=false: files still being chunked by the archive thread')

# 2) 보관 스레드: archive(지점 파일을 staging 에서) + collect 를 차례로
rep('static bool expand(const File& f,std::vector<unsigned char>& out){',
    r'''// Claude 10-27: the capture runs on the script thread once per message. Only the native save has to happen there; its
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
static void drainAll(){if(aStarted){AcquireSRWLockExclusive(&aLock);while(!aQueue.empty()||aBusy)SleepConditionVariableSRW(&aIdle,&aLock,INFINITE,0);ReleaseSRWLockExclusive(&aLock);}drain();}
static bool expand(const File& f,std::vector<unsigned char>& out){''')

# 3) stage·load·saveReference 는 다 기다림
rep('static bool stage(const Point& cp){drain();clearScratch();', 'static bool stage(const Point& cp){drainAll();clearScratch();')
rep('static int load(){bool isJump=*(int*)0x5b3ec4==Poll;', 'static int load(){drainAll();bool isJump=*(int*)0x5b3ec4==Poll;')
rep('static void saveReference(int slot,int ok){if(ok&&slot>0&&init()){', 'static void saveReference(int slot,int ok){if(ok&&slot>0&&init()){drainAll();')

# 4) capture: 앞 지점 봉인은 보관이 끝난 지점만 바로 기록(아니면 보관 스레드가 봉인 상태로 씀)
rep('if(open&&!points.empty()){points.back().end=n;points.back().sealed=true;savePoint(points.back());open=false;}',
    'if(open&&!points.empty()){points.back().end=n;points.back().sealed=true;if(points.back().archived)savePoint(points.back());open=false;}')
# 엔진 저장 뒤: 파일을 staging 으로 옮기고 보관 스레드에 넘김
rep(' if(ok&&archive(cp)){N2HD_Trace(112);points.push_back(cp);liveId=cp.id;open=true;++captured;head();double jt3=jtNow();if(captured==1||captured%64==0)collect();double jt4=jtNow();}else{setId(oldId);++errors;ok=0;}',
    ' bool staged=false;\n'
    ' if(ok){std::vector<std::string> files={"0001\\\\script.npf","0001\\\\frames.npf","0001\\\\bklg.npf","0001\\\\val.npf"};for(const auto& f:names(work+"\\\\images","0001_*.npf"))files.push_back("images\\\\"+f);\n'
    '  std::string sd=root+"\\\\staging\\\\"+cp.id;staged=dir(root+"\\\\staging")&&dir(sd)&&dir(sd+"\\\\0001")&&dir(sd+"\\\\images");double tr=jtNow();\n'
    '  for(const auto& f:files)if(staged&&!MoveFileExW(wp(work+"\\\\"+f).c_str(),wp(sd+"\\\\"+f).c_str(),MOVEFILE_REPLACE_EXISTING))staged=false;jtRead+=jtNow()-tr;\n'
    '  if(staged){cp.archived=false;ArchiveJob job;job.id=cp.id;job.dir=sd;job.files=files;staged=enqueueArchive(std::move(job));}}\n'
    ' if(staged){N2HD_Trace(112);points.push_back(cp);liveId=cp.id;open=true;++captured;head();if(captured==1||captured%64==0){ArchiveJob c;c.collect=true;enqueueArchive(std::move(c));}}else{setId(oldId);++errors;ok=0;}')
# 5) seal: 보관 중인 지점은 보관 스레드가 봉인 상태로 기록
rep('static int seal(){Lock guard;if(!points.empty()&&open){auto& p=points.back();p.end=historySize();p.sealed=true;open=false;if(!savePoint(p))++errors;}return 1;}',
    'static int seal(){Lock guard;if(!points.empty()&&open){auto& p=points.back();p.end=historySize();p.sealed=true;open=false;if(p.archived&&!savePoint(p))++errors;}return 1;}')
p.write_text(s, 'utf-8')
print('ok')
