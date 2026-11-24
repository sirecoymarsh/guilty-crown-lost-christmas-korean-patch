"""대사 기록 점프: 새 조각 압축·쓰기를 일꾼 스레드로(지점 저장 130ms 중 82ms). 조각을 읽는 곳(stage)·정리(collect)는 먼저 기다림. 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\backlog_jump.inc'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:70], s.count(old))
    s = s.replace(old, new)


old_chunk = s[s.index('static bool chunk(const unsigned char* p,size_t n,std::string& h){'):]
old_chunk = old_chunk[:old_chunk.index('\n') + 1]
new_chunk = r'''// Claude 10-27: new blocks are compressed and written by a worker thread. The capture runs on the script thread once
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
'''
s = s.replace(old_chunk, new_chunk, 1)
rep('static bool stage(const Point& cp){clearScratch();', 'static bool stage(const Point& cp){drain();clearScratch();')
rep('static void collect(){\n', 'static void collect(){\n drain();wKnown.clear();   // blocks may be deleted below; let chunk() look on disk again\n')
if '#include <deque>' not in s:
    rep('#include <compressapi.h>', '#include <compressapi.h>\n#include <deque>')
p.write_text(s, 'utf-8')
print('ok')
