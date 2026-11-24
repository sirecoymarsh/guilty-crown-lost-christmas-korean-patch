"""시험 계측: 대사 기록 점프 지점 저장(capture)의 단계별 시간을 N2HD_PROFILE_DIR\\jump.log 에. 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\backlog_jump.inc'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:70], s.count(old))
    s = s.replace(old, new)


rep('static std::string sha(const unsigned char* p,size_t n){',
    '// Test timing (Claude 10-27): where a checkpoint capture spends its time.\n'
    'static double jtSha,jtWrite,jtRead;static unsigned jtNew;\n'
    'static double jtNow(){static LARGE_INTEGER f;LARGE_INTEGER c;if(!f.QuadPart)QueryPerformanceFrequency(&f);QueryPerformanceCounter(&c);return c.QuadPart*1000.0/f.QuadPart;}\n'
    'static std::string sha(const unsigned char* p,size_t n){')
rep('static bool chunk(const unsigned char* p,size_t n,std::string& h){h=sha(p,n);if(h.size()!=64)return false;std::string path=root+"\\\\blocks\\\\"+h+".blk";if(GetFileAttributesW(wp(path).c_str())!=INVALID_FILE_ATTRIBUTES)return true;',
    'static bool chunk(const unsigned char* p,size_t n,std::string& h){double t0=jtNow();h=sha(p,n);jtSha+=jtNow()-t0;if(h.size()!=64)return false;std::string path=root+"\\\\blocks\\\\"+h+".blk";if(GetFileAttributesW(wp(path).c_str())!=INVALID_FILE_ATTRIBUTES)return true;t0=jtNow();++jtNew;struct W{double t0;~W(){jtWrite+=jtNow()-t0;}}w{t0};')
rep('if(!safeName(n))return false;std::vector<unsigned char>b;if(!read(work+"\\\\"+n,b))return false;',
    'if(!safeName(n))return false;std::vector<unsigned char>b;double tr=jtNow();if(!read(work+"\\\\"+n,b))return false;jtRead+=jtNow()-tr;')
rep('cp.prefix=historyHash(n);std::string oldId=savedId();setId(cp.id);resetId=false;clearScratch();char old[260];strcpy_s(old,(char*)0x5a54b4);strcpy_s((char*)0x5a54b4,260,work.c_str());int ok=nativeSave(1);strcpy_s((char*)0x5a54b4,260,old);',
    'cp.prefix=historyHash(n);std::string oldId=savedId();setId(cp.id);resetId=false;double jt0=jtNow();clearScratch();double jt1=jtNow();char old[260];strcpy_s(old,(char*)0x5a54b4);strcpy_s((char*)0x5a54b4,260,work.c_str());int ok=nativeSave(1);strcpy_s((char*)0x5a54b4,260,old);double jt2=jtNow();jtSha=jtWrite=jtRead=0;jtNew=0;')
rep('if(captured==1||captured%64==0)collect();}else{setId(oldId);++errors;ok=0;}clearScratch();lastCaptureMs=GetTickCount64()-t;return ok;',
    'double jt3=jtNow();if(captured==1||captured%64==0)collect();double jt4=jtNow();}else{setId(oldId);++errors;ok=0;}double jt5=jtNow();clearScratch();lastCaptureMs=GetTickCount64()-t;\n'
    ' {char d[MAX_PATH];if(GetEnvironmentVariableA("N2HD_PROFILE_DIR",d,MAX_PATH)){char path[MAX_PATH];sprintf_s(path,"%s\\\\jump.log",d);FILE* f=0;if(!fopen_s(&f,path,"a")&&f){'
    'fprintf(f,"capture total=%.0f clear=%.0f save=%.0f read=%.0f sha=%.0f write=%.0f new=%u archive+collect=%.0f clear2=%.0f raw=%llu\\n",jtNow()-jt0,jt1-jt0,jt2-jt1,jtRead,jtSha,jtWrite,jtNew,jt5-jt2,jtNow()-jt5,(unsigned long long)rawBytes);fclose(f);}}}\n'
    ' return ok;')
p.write_text(s, 'utf-8')
print('ok')
