"""진단(한 번만): 합본 소스 사본에 기록을 넣어 엔진이 쪽을 넘길 때 글 창(4K 사본이 있는 면)을 어떻게 지우는지 본다.
- copy.log: 모든 0x468700(M)·0x48c900(c) 복사 — 원본에 4K 사본이 없는 것도. 원본 1배 알파 칸 수, 대상 사본 유무, 프레임.
- surf.log: 4K 사본이 있는 면마다 프레임별 1배 알파 칸 수가 바뀔 때.
결과 DLL: merge_1101\\diag_build\\n2hd_runtime.dll (N2HD_GLYPH_LOG + N2HD_PROFILE_DIR 일 때만 기록)"""
import shutil
from pathlib import Path

SRC = Path(r'F:\AI\gclx-4k\engine\merge_1101\src')
DIAG = Path(r'F:\AI\gclx-4k\engine\merge_1101\diag_src')
if DIAG.exists():
    shutil.rmtree(DIAG)
shutil.copytree(SRC, DIAG)
p = DIAG / 'n2hd_gpu_v8.cpp'
s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:60], s.count(old))
    s = s.replace(old, new)


rep('static void copyGlyph(void* dst,void* src,int x,int y,uint32_t color,bool overwrite){\n',
    'static FILE* diagFile(const wchar_t* name){wchar_t d[MAX_PATH];if(!GetEnvironmentVariableW(L"N2HD_GLYPH_LOG",0,0)||!GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",d,MAX_PATH))return 0;return _wfopen((std::wstring(d)+L"\\\\"+name).c_str(),L"a");}\n'
    'static int alphaCount(void* t){if(!t)return -1;uint32_t** rows=(uint32_t**)pv(t,0x2c);int w=iv(t,8),h=iv(t,12);if(!rows||w<1||h<1||w>4096||h>4096)return -1;int n=0;for(int y=0;y<h;++y){if(!rows[y])return -2;for(int x=0;x<w;++x)if(rows[y][x]>>24)++n;}return n;}\n'
    'static void copyGlyph(void* dst,void* src,int x,int y,uint32_t color,bool overwrite){\n'
    ' {static FILE* cf=diagFile(L"copy.log");if(cf&&dst&&src){void* sk=pv(src,0x28);void* dk=pv(dst,0x28);bool sh=high.count(sk)!=0;fprintf(cf,"f=%llu %c src=%p %dx%d hi=%d a=%d dst=%p %dx%d dsthi=%d at=%d,%d color=%08x\\n",(unsigned long long)frames,overwrite?\'M\':\'c\',sk,iv(src,8),iv(src,12),sh?1:0,sh?0:alphaCount(src),dk,iv(dst,8),iv(dst,12),high.count(dk)?1:0,x,y,color);fflush(cf);}}\n')
rep(' void* t=pv(object,0x2c);void* m=pv(object,0x28);int* clip=(int*)pv(object,0x24);if(!t||!m||!clip)return;int sw=iv(t,8),sh=iv(t,12);if(sw<1||sh<1)return;IDirect3DTexture9* tex=upload(t);if(!tex)return;\n',
    ' void* t=pv(object,0x2c);void* m=pv(object,0x28);int* clip=(int*)pv(object,0x24);if(!t||!m||!clip)return;int sw=iv(t,8),sh=iv(t,12);if(sw<1||sh<1)return;IDirect3DTexture9* tex=upload(t);if(!tex)return;\n'
    ' {static FILE* sf=diagFile(L"surf.log");static std::unordered_map<void*,int> lastA;void* dk=pv(t,0x28);if(sf&&high.count(dk)){int a=alphaCount(t);auto it=lastA.find(dk);if(it==lastA.end()||it->second!=a){fprintf(sf,"f=%llu surf=%p %dx%d alpha=%d was=%d\\n",(unsigned long long)frames,dk,sw,sh,a,it==lastA.end()?-9:it->second);fflush(sf);lastA[dk]=a;}}}\n')
p.write_text(s, 'utf-8')
b = (Path(r'F:\AI\gclx-4k\engine\merge_1101\build.cmd')).read_text('utf-8')
b = b.replace(r'merge_1101\src', r'merge_1101\diag_src').replace(r'merge_1101\build', r'merge_1101\diag_build')
(Path(r'F:\AI\gclx-4k\engine\merge_1101\build_diag.cmd')).write_text(b, 'utf-8')
print('ok')
