"""Claude 10-27 고침을 코덱스 배포 엔진(release-language-review-20261028, DLL 433a93ef)에 얹은 합본 소스를 만든다(사용자 11-01 「Merge it here」).
얹는 것:
 ① 글 창 줄 구간(+0xf0)을 4K 로 그림(patch_row_spans) — 「덮」의 ㅓ 등 흐림
 ② 테두리 짝 넓히기(patch_outline_pairs) — 테두리가 여러 겹으로 갈라짐
 ③ 1배 그림 캐시(img_cache.inc, PNG·JPEG 해독 결과 보관) — 점프·장면 바뀔 때 멈춤
 ④ 점프 지점 저장 동안 건너뛰기·자동 끄기(save-quiet) — 코덱스의 「불러온 뒤 0x480cb0」와 함께 둠
 ⑤ 코덱스 font-stroke-clarity-20261029 의 대사 기록 미리 곱하기(premultiply)+ONE 혼합(그 판의 나머지는 안 씀)
코덱스 폴더는 읽기만. 결과: F:\\AI\\gclx-4k\\engine\\merge_1101\\src → build.cmd → ..\\build\\n2hd_runtime.dll
"""
import shutil
from pathlib import Path

REV = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions')
BASE = REV / 'release-language-review-20261028' / 'engine'
STROKE = REV / 'font-stroke-clarity-20261029' / 'engine'
MINE = Path(r'F:\AI\gclx-4k\engine\src')
OUT = Path(r'F:\AI\gclx-4k\engine\merge_1101')
SRC = OUT / 'src'

if SRC.exists():
    shutil.rmtree(SRC)
SRC.mkdir(parents=True)
for p in BASE.iterdir():
    if p.suffix in ('.cpp', '.h', '.inc'):
        shutil.copyfile(p, SRC / p.name)
shutil.copyfile(MINE / 'img_cache.inc', SRC / 'img_cache.inc')


def rd(p):
    return p.read_text('utf-8')


def sub(text, old, new, name):
    assert text.count(old) == 1, (name, text.count(old), old[:80])
    return text.replace(old, new, 1)


def between(text, start, end):
    """text 안 start 로 시작해 end 로 끝나는 첫 덩어리(양끝 포함)."""
    i = text.index(start)
    j = text.index(end, i) + len(end)
    return text[i:j]


# ①② n2hd_gpu_v8.cpp — 내 판의 해당 덩어리를 그대로 옮김(측정기 줄은 코덱스 그대로)
g, m = rd(SRC / 'n2hd_gpu_v8.cpp'), rd(MINE / 'n2hd_gpu_v8.cpp')
helpers = between(m, 'static void copyInto(', 'out[y*s.w+x]=m<<24;}}\n')
g = sub(g, 'static void copyGlyph(void* dst,void* src,int x,int y,uint32_t color,bool overwrite){',
        helpers + 'static void copyGlyph(void* dst,void* src,int x,int y,uint32_t color,bool overwrite){', 'helpers')
old_copy = between(g, ' source=high.find(pv(src,0x28));Hi &s=source->second', 'd.version=++serial;++copies;')
new_copy = between(m, ' source=high.find(pv(src,0x28));Hi &s=source->second', 'd.version=++serial;++copies;')
g = sub(g, old_copy, new_copy, 'copyGlyph')
g = sub(g, 'static bool needsCompatibility(void* o,void* arg,void* filter){if(arg)return true;void* m=pv(o,0x28);if(m&&pv(m,0xf0))return true;',
        between(m, '// Row clip spans (+0xf0) are drawn', 'if(m&&pv(m,0xf0)&&spanCompat())return true;'), 'needsCompatibility')
g = sub(g, ' dev->SetScissorRect(&rc);dev->SetTexture(0,tex);lastError=dev->DrawPrimitiveUP(D3DPT_TRIANGLEFAN,2,v,sizeof(V));if(SUCCEEDED(lastError))++draws;\n',
        between(m, ' dev->SetTexture(0,tex);short* spans=(short*)pv(m,0xf0);', '  row=end;}\n'), 'spans')
# ⑥ 쪽이 바뀌면 4K 사본도 비움(합본 시험에서 찾음 11-01: 앞 쪽 글자 꼬리·루비가 새 쪽 뒤에 남음).
#    엔진은 쪽마다 같은 글 면을 다시 쓰고 1배 면을 여기 갈고리 없는 길로 통째로 지운다(진단 diag_clear_1101.py: 1953칸→0, 그 사이 복사 없음).
#    1배 면에 잉크가 하나도 없으면 4K 사본을 비운다 — 복사 직전·그리기 직전. 4K 사본이 없는 원본(빈칸 등)의 복사도 4K 사본에 1배 그대로 옮긴다.
g = sub(g, 'struct Hi {int w=0,h=0;uint64_t version=0;std::vector<uint32_t> data;};',
        'struct Hi {int w=0,h=0;uint64_t version=0;std::vector<uint32_t> data;bool blank=false;};', 'Hi.blank')
g = sub(g, 'static void copyInto(',
        '// Text surfaces are reused from page to page: the engine wipes the 1x surface without the copies hooked here and draws\n'
        '// the next page into it, so the 4x copy kept the last page under the new one (merged build, 11-01). A 4x copy whose 1x\n'
        '// surface has no ink left is emptied, checked before each copy into it and before it is drawn.\n'
        'static bool inkless(void* t){uint32_t** rows=(uint32_t**)pv(t,0x2c);int w=iv(t,8),h=iv(t,12);if(!rows||w<1||h<1||w>4096||h>4096)return false;\n'
        ' for(int y=0;y<h;++y){if(!rows[y])return false;for(int x=0;x<w;++x)if(rows[y][x]>>24)return false;}return true;}\n'
        'static void wipeIfInkless(void* t,Hi& d){if(d.blank||!inkless(t))return;std::fill(d.data.begin(),d.data.end(),0u);d.blank=true;d.version=++serial;}\n'
        '// A copy from a surface with no 4x glyph (a space, a blank) into a 4x copy: the 1x pixels, 4x4 each, as the engine writes them.\n'
        'static void copyPlain(Hi& d,void* dst,void* src,int x,int y,uint32_t color,bool overwrite){wipeIfInkless(dst,d);uint32_t** rows=(uint32_t**)pv(src,0x2c);int sw=iv(src,8),sh=iv(src,12);if(!rows||sw<1||sh<1||sw>4096||sh>4096)return;\n'
        ' bool wrote=false,ink=false;for(int yy=std::max(0,-y*4);yy<sh*4&&y*4+yy<d.h;++yy){const uint32_t* r=rows[yy/4];if(!r)return;for(int xx=std::max(0,-x*4);xx<sw*4&&x*4+xx<d.w;++xx){uint32_t p=r[xx/4];if(overwrite||(p>>24)){d.data[(y*4+yy)*d.w+x*4+xx]=(p&0xff000000)|(color&0xffffff);wrote=true;if(p>>24)ink=true;}}}\n'
        ' if(ink)d.blank=false;if(wrote)d.version=++serial;}\n'
        'static void copyInto(', 'wipe helpers')
g = sub(g, ' if(!dst||!src)return;auto source=high.find(pv(src,0x28));if(source==high.end())return;void* key=pv(dst,0x28);',
        ' if(!dst||!src)return;auto source=high.find(pv(src,0x28));void* key=pv(dst,0x28);\n'
        ' if(source==high.end()){auto dh=key?high.find(key):high.end();if(dh!=high.end())copyPlain(dh->second,dst,src,x,y,color,overwrite);return;}\n', 'plain copies')
g = sub(g, 'Hi &s=source->second,&d=high.find(key)->second;int ox=x*4,oy=y*4;\n',
        'Hi &s=source->second,&d=high.find(key)->second;int ox=x*4,oy=y*4;wipeIfInkless(dst,d);\n', 'wipe before copy')
g = sub(g, '  if(pair){auto pd=high.find(last.dst);if(pd!=high.end()){widen(s,wide);copyInto(pd->second,wide.data(),s.w,s.h,last.x*4,last.y*4,last.color,last.overwrite);pd->second.version=++serial;}}}\n',
        '  if(pair){auto pd=high.find(last.dst);if(pd!=high.end()){widen(s,wide);copyInto(pd->second,wide.data(),s.w,s.h,last.x*4,last.y*4,last.color,last.overwrite);pd->second.blank=false;pd->second.version=++serial;}}}\n', 'pair blank')
g = sub(g, ' d.version=++serial;++copies;', ' d.blank=false;d.version=++serial;++copies;', 'copy blank')
g = sub(g, 'if(sw<1||sh<1)return;IDirect3DTexture9* tex=upload(t);',
        'if(sw<1||sh<1)return;{auto hw=high.find(pv(t,0x28));if(hw!=high.end())wipeIfInkless(t,hw->second);}IDirect3DTexture9* tex=upload(t);', 'wipe before draw')
# ⑧ F8 화질 [4K · 그림 원본 · 원본] (사용자 11-01 「4K와 원본을 스위칭할 방법은 없나?」; 본체는 quality_switch.inc).
shutil.copyfile(Path(__file__).with_name('quality_switch.inc'), SRC / 'quality_switch.inc')
g = sub(g, '#include "hires_art.inc"\n',
        'static volatile LONG gQuality=0;static void qualityInit();static void qualityRelease();   // F8 picture quality (quality_switch.inc)\n'
        '#include "hires_art.inc"\n', 'quality decl')
g = sub(g, 'if(m&&pv(m,0xf0)&&spanCompat())return true;',
        'if(m&&pv(m,0xf0)&&(spanCompat()||gQuality>=2))return true;if(gQuality>=2){void* tt=pv(o,0x2c);if(tt&&high.count(pv(tt,0x28)))return true;}', 'quality text')
g = sub(g, 'static void releaseGpu(){Backlog::release();artRelease();', 'static void releaseGpu(){Backlog::release();artRelease();qualityRelease();', 'quality release')
g = sub(g, 'void __cdecl N2HD_Clear(){Guard guard;PerfScope perf(PF_CLEAR);if(ensure()){', 'void __cdecl N2HD_Clear(){Guard guard;PerfScope perf(PF_CLEAR);qualityInit();if(ensure()){', 'quality init')
g = sub(g, '#include "backlog_renderer.inc"\n', '#include "backlog_renderer.inc"\n#include "quality_switch.inc"\n', 'quality include')
g = sub(g, 'void __cdecl N2HD_End(){Guard guard;PerfScope perf(PF_END);', 'void __cdecl N2HD_End(){Guard guard;PerfScope perf(PF_END);InterlockedExchange(&gRendering,0);', 'quality end')
g = sub(g, 'presentResult=dev->Present(0,0,0,0);', 'qualityOverlay();presentResult=dev->Present(0,0,0,0);', 'quality overlay')
# 시험 전용: N2HD_TEST_SHOT_START_MS 뒤부터 찍기(짧은 간격으로 한 구간만 볼 때; N2HD_PROFILE_DIR 있을 때만 찍힘은 그대로)
g = sub(g, 'if(every<=0||shots>=60)return;',
        'static DWORD shotT0=0,shotDelay=(DWORD)-1;if(shotDelay==(DWORD)-1){wchar_t sv[32];shotDelay=GetEnvironmentVariableW(L"N2HD_TEST_SHOT_START_MS",sv,32)?(DWORD)_wtoi(sv):0;}if(!shotT0)shotT0=now;'
        'if(every<=0||shots>=60||now-shotT0<shotDelay)return;', 'shot start')
(SRC / 'n2hd_gpu_v8.cpp').write_text(g, 'utf-8')
# ⑨ 메뉴를 열 때 잠깐 1배(사용자 11-01 「세이브같은 메뉴 띄울때 잠깐 4K 업스케일이 풀리는 버그」): 메뉴 대본의
#    CreateTexture(…, SCREEN/VIDEO) 는 그림 불러오기(0x467990)에 이름 "SCREEN"/"VIDEO" 로 1배 화면을 복사한다(S 키 세이브·불러오기·
#    대사 기록·종료 확인 등은 VIDEO, 오른쪽 클릭 메뉴에서 오면 SCREEN; 0x441080 캡처 갈고리를 안 거침;
#    진단 diag_menu_1101.py). 다음 그리기 직전에 4K 백 버퍼(지금 화면)를 그 면의 스냅숏으로 복사한다 — N2HD_Capture 와 같은 방식.
g = sub(g, 'static volatile LONG gQuality=0;',
        'static std::vector<void*> screenWanted;static void screenPending(void* t);   // SCREEN pictures (below N2HD_Clear)\n'
        'static volatile LONG gQuality=0;', 'screen decl')
g = sub(g, 'VideoStop(data);hdMovies.erase(t);', 'VideoStop(data);hdMovies.erase(t);screenWanted.erase(std::remove(screenWanted.begin(),screenWanted.end(),t),screenWanted.end());', 'screen forget')
g = sub(g, 'extern "C" __declspec(dllexport) void __cdecl N2HD_Clear(){',
        '// CreateTexture(…, SCREEN) copies the engine\'s 1x frame (the save and menu backgrounds), so a menu opened at 1x for a\n'
        '// moment (user 11-01). The picture loader is asked for "SCREEN"; at the start of the next render, before anything is\n'
        '// drawn, the 4K back buffer (the frame on screen) becomes that texture\'s snapshot, as in N2HD_Capture.\n'
        'static void screenPending(void* t){if(t&&iv(t,8)==1024&&iv(t,12)==576)screenWanted.push_back(t);}\n'
        'static void screenTake(){if(screenWanted.empty())return;IDirect3DSurface9* src=0;if(FAILED(dev->GetBackBuffer(0,0,D3DBACKBUFFER_TYPE_MONO,&src))){screenWanted.clear();return;}\n'
        ' if(begun){dev->EndScene();begun=false;}\n'
        ' for(void* t:screenWanted){auto it=snapshots.find(t);IDirect3DTexture9* dst=it==snapshots.end()?0:it->second;\n'
        '  if(!dst){if(FAILED(dev->CreateTexture(W,H,1,D3DUSAGE_RENDERTARGET,D3DFMT_X8R8G8B8,D3DPOOL_DEFAULT,&dst,0)))continue;snapshots[t]=dst;}\n'
        '  IDirect3DSurface9* s=0;dst->GetSurfaceLevel(0,&s);lastError=dev->StretchRect(src,0,s,0,D3DTEXF_NONE);s->Release();if(SUCCEEDED(lastError))++captures;}\n'
        ' src->Release();screenWanted.clear();}\n'
        'extern "C" __declspec(dllexport) void __cdecl N2HD_Clear(){', 'screen take def')
g = sub(g, 'void __cdecl N2HD_Clear(){Guard guard;PerfScope perf(PF_CLEAR);qualityInit();if(ensure()){',
        'void __cdecl N2HD_Clear(){Guard guard;PerfScope perf(PF_CLEAR);qualityInit();if(ensure()){screenTake();', 'screen take call')
(SRC / 'n2hd_gpu_v8.cpp').write_text(g, 'utf-8')
h_art = (SRC / 'hires_art.inc').read_text('utf-8')
h_art = sub(h_art, ' if(!name||!t)return;if(!artIndexLoaded)artLoadIndex();',
            ' if(name&&t&&(!_stricmp(name,"SCREEN")||!_stricmp(name,"VIDEO")))screenPending(t);   // menu backdrops: S-key save, load, backlog, close… use VIDEO; the right-click path SCREEN\n if(!name||!t)return;if(!artIndexLoaded)artLoadIndex();', 'screen hook')
h_art = sub(h_art, 'static IDirect3DTexture9* artTexture(void* t){void* data=pv(t,0x28);',
            'static IDirect3DTexture9* artTexture(void* t){if(gQuality>=1)return 0;void* data=pv(t,0x28);', 'quality art')
(SRC / 'hires_art.inc').write_text(h_art, 'utf-8')

# ③ runtime_hooks.cpp + native_hook_manifest.h — 그림 캐시
r, mr = rd(SRC / 'runtime_hooks.cpp'), rd(MINE / 'runtime_hooks.cpp')
r = sub(r, 'static void* origLoadImage;\n', 'static void* origLoadImage;\n#include "img_cache.inc"\n', 'include')
old_load = between(r, '__declspec(naked) static void hookLoadImage(){__asm {', '}}')
new_load = between(mr, '__declspec(naked) static void hookLoadImage(){__asm {', '}}')
decoders = between(mr, '// The engine\'s PNG and JPEG decoders (see img_cache.inc).', ' popad\n ret\n}}\n')
r = sub(r, old_load, new_load + '\n' + decoders.rstrip('\n'), 'hookLoadImage+decoders')
# ⑩ 단추 판정이 Zoom 을 무시해 축소한 4배 글자 그림의 보이지 않는 큰 사본이 단추가 되던 것(사용자 11-02 「타이틀에서 뭘 눌러도 새 게임」·
#    「메뉴 한참 아래에도 손모양」): 엔진 판정 고리 0x452715 를 hit_zoom.inc 로(그려진 사각형 기준으로 텍셀을 찾음).
shutil.copyfile(Path(__file__).with_name('hit_zoom.inc'), SRC / 'hit_zoom.inc')
g2 = (SRC / 'n2hd_gpu_v8.cpp').read_text('utf-8')
g2 = sub(g2, '#include "quality_switch.inc"\n', '#include "quality_switch.inc"\n#include "hit_zoom.inc"\n', 'hit include')
(SRC / 'n2hd_gpu_v8.cpp').write_text(g2, 'utf-8')
r = sub(r, '// The engine\'s PNG and JPEG decoders (see img_cache.inc).',
        '// The choice hit test (hit_zoom.inc): 0x452715, inside the loop over a button\'s MouseUsual pictures; edx is the picture,\n'
        '// [esp+0x20] the list node, [esp+0x24] the event with the pointer at +0x28/+0x2c. A hit goes on at 0x45282f, a miss at 0x4527ad.\n'
        'extern "C" int __cdecl N2HD_HitTest(void*,int,int,void*);\n'
        'static void* origHitTest;static void* hitYes=(void*)0x45282f;static void* hitNo=(void*)0x4527ad;\n'
        '__declspec(naked) static void hookHitTest(){__asm {\n'
        ' mov eax,dword ptr [esp+0x24]\n mov ecx,dword ptr [esp+0x20]\n push ecx\n push dword ptr [eax+0x2c]\n push dword ptr [eax+0x28]\n push edx\n'
        ' call N2HD_HitTest\n add esp,16\n test eax,eax\n jnz yes\n jmp dword ptr [hitNo]\nyes:\n jmp dword ptr [hitYes]\n}}\n'
        '// The engine\'s PNG and JPEG decoders (see img_cache.inc).', 'hit stub')
h_hit = (SRC / 'native_hook_manifest.h').read_text('utf-8')
h_hit = sub(h_hit, '\n};', '\n{0x452715,(void*)&hookHitTest,&origHitTest,7,{0x8b,0x44,0x24,0x24,0x8b,0x48,0x28},0,0},\n};', 'hit manifest')
(SRC / 'native_hook_manifest.h').write_text(h_hit, 'utf-8')
# 시험 전용 가짜 커서(quality_switch.inc)를 시작 때 — 원래 1배 시험(N2HD_TEST_NATIVE)에서도 쓰이게
r = sub(r, 'loadPrivateFonts();redirectProfileForTests();',
        'loadPrivateFonts();redirectProfileForTests();N2HD_TestCursorInit();', 'test cursor install')
r = sub(r, 'extern "C" __declspec(dllexport) DWORD WINAPI N2HD_RemoteInstall(',
        'extern "C" __declspec(dllexport) DWORD WINAPI N2HD_RemoteInstall(', 'noop')
r = sub(r, 'static void redirectProfileForTests(){',
        'extern "C" void __cdecl N2HD_TestCursorInit();\nstatic void redirectProfileForTests(){', 'test cursor decl')
(SRC / 'runtime_hooks.cpp').write_text(r, 'utf-8')
h, mh = rd(SRC / 'native_hook_manifest.h'), rd(MINE / 'native_hook_manifest.h')
lines = [l for l in mh.splitlines(True) if l.startswith('{0x46d670,') or l.startswith('{0x469b20,')]
assert len(lines) == 2
anchor = [l for l in h.splitlines(True) if l.startswith('{0x467990,')]
assert len(anchor) == 1, anchor
h = sub(h, anchor[0], anchor[0] + ''.join(lines), 'manifest')
(SRC / 'native_hook_manifest.h').write_text(h, 'utf-8')

# ④ backlog_jump.inc — 저장 동안 건너뛰기 끄기(코덱스의 불러온 뒤 고침·잠금은 그대로)
j, mj = rd(SRC / 'backlog_jump.inc'), rd(MINE / 'backlog_jump.inc')
quiet = between(mj, ' // Checkpoints are taken with skip, auto and the express skip off', 'if(quiet)for(int i=0;i<6;++i)if(quietPtr[i])*(double*)(quietPtr[i]+0x10)=quietOld[i];\n')
j = sub(j, ' int ok=nativeSave(1);if(tsv)*(double*)(tsv+0x10)=tso;',
        quiet + ' if(tsv)*(double*)(tsv+0x10)=tso;', 'save-quiet')
# ⑪ 시나리오 열람(kr_scenario.nss)이 장면 하나를 재생하는 동안($KR_REPLAY)은 대화 기록 점프 지점을 만들지도, 점프하지도 않는다
#    (점프는 엔진 불러오기로 본편 상태를 되살려 열람 밖으로 나간다).
j = sub(j, 'static int __cdecl jumpCapture(){static int off=-1;if(off<0)off=GetEnvironmentVariableA("N2HD_TEST_NO_JUMP",0,0)?1:0;if(off)return 1;return Jump::capture();}',
        '// Scenario viewer playback (kr_scenario.nss sets $KR_REPLAY): no checkpoints and no backlog jumps, which would load the\n'
        '// story state and leave the viewer.\n'
        'static bool replaying(){auto v=Jump::var("$KR_REPLAY");return v&&*(double*)(v+0x10)!=0.0;}\n'
        'static int __cdecl jumpCapture(){static int off=-1;if(off<0)off=GetEnvironmentVariableA("N2HD_TEST_NO_JUMP",0,0)?1:0;if(off||replaying())return 1;return Jump::capture();}', 'replay capture')
j = sub(j, 'static int __cdecl jumpSeal(){return Jump::seal();}', 'static int __cdecl jumpSeal(){if(replaying())return 1;return Jump::seal();}', 'replay seal')
j = sub(j, 'static int __cdecl jumpPoll(){return Jump::poll();}', 'static int __cdecl jumpPoll(){if(replaying())return 0;return Jump::poll();}', 'replay poll')
(SRC / 'backlog_jump.inc').write_text(j, 'utf-8')

# ⑤ backlog_renderer.inc — 코덱스 미리 곱하기 판 그대로
assert rd(BASE / 'backlog_renderer.inc') != rd(STROKE / 'backlog_renderer.inc')
shutil.copyfile(STROKE / 'backlog_renderer.inc', SRC / 'backlog_renderer.inc')

# ⑦ 巨獣 「거대한 짐승」(사용자 11-01, 코덱스 오프라인이라 Claude 반영): 대사 기록 루비 표 두 줄. 대본은 tools\apply_geosu.py.
import importlib.util
_spec = importlib.util.spec_from_file_location('ruby_map_geosu', Path(__file__).with_name('ruby_map_geosu.py'))
_rm = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_rm)
_h, _changed = _rm.apply((SRC / 'backlog_ruby_map.h').read_text('ascii'))
(SRC / 'backlog_ruby_map.h').write_text(_h, 'ascii')

(OUT / 'build.cmd').write_text(r'''@echo off
rem 합본: 코덱스 release-language-review-20261028 엔진 + Claude 10-27 고침(merge_codex_1101.py).
set TEMP=F:\AI\gclx-4k\engine\temp
set TMP=%TEMP%
if not exist "%TEMP%" mkdir "%TEMP%"
if not exist "F:\AI\gclx-4k\engine\merge_1101\build" mkdir "F:\AI\gclx-4k\engine\merge_1101\build"
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
set JXL=P:\AI\Codex\projects\reconquista_flowchart_20261024\build\libjxl-x86
cd /d F:\AI\gclx-4k\engine\merge_1101\src
cl /nologo /LD /O2 /MT /EHsc /W3 /arch:SSE2 /std:c++17 /utf-8 /I "%JXL%\lib\include" /Fo"F:\AI\gclx-4k\engine\temp\\" n2hd_gpu_v8.cpp runtime_hooks.cpp media_backend.cpp d3d9.lib gdi32.lib user32.lib d3dcompiler.lib bcrypt.lib cabinet.lib mfplat.lib mfreadwrite.lib mfuuid.lib ole32.lib dxva2.lib winmm.lib "%JXL%\lib\jxl_dec.lib" "%JXL%\lib\jxl_threads.lib" "%JXL%\third_party\highway\hwy.lib" "%JXL%\third_party\brotli\brotlidec.lib" "%JXL%\third_party\brotli\brotlicommon.lib" /link /OUT:F:\AI\gclx-4k\engine\merge_1101\build\n2hd_runtime.dll /INCREMENTAL:NO
''', 'utf-8')
print('합본 소스 →', SRC)
