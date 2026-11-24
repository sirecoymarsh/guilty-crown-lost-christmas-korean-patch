#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <d3d9.h>
#include <d3dcompiler.h>
#include <unordered_set>
#include <stdint.h>
#include <algorithm>
#include <vector>
#include <unordered_map>
#include "media_backend.h"
namespace Backlog {static void release();}
static CRITICAL_SECTION rendererLock;struct Guard{Guard(){EnterCriticalSection(&rendererLock);}~Guard(){LeaveCriticalSection(&rendererLock);}};
// Claude 10-27: time spent inside the renderer, by entry point and per frame (written to the test log as "stat" lines).
enum {PF_DRAW,PF_GLYPH,PF_COPY,PF_CAPTURE,PF_CLEAR,PF_END,PF_PRESENT,PF_MOVIE,PF_LOAD,PF_BACKLOG,PF_N};
// Event ring for the long-frame trace: (time, slot*2 + 0 enter / 1 leave, thread).
struct TraceEv{LONGLONG t;int id;DWORD tid;};static TraceEv traceRing[8192];static volatile LONG traceN;
static bool traceOn(){static const bool on=GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",0,0)!=0;return on;}
static void traceEv(int id){if(!traceOn())return;LONG i=InterlockedIncrement(&traceN)-1;LARGE_INTEGER q;QueryPerformanceCounter(&q);TraceEv& e=traceRing[i&8191];e.t=q.QuadPart;e.id=id;e.tid=GetCurrentThreadId();}
extern "C" void __cdecl N2HD_Trace(int id){traceEv(id);}static LONGLONG pfTotal[PF_N],pfFrame,pfFrameMax,pfFreq;static uint64_t pfOver16,pfOver50;
// Only test runs (N2HD_PROFILE_DIR) time and trace; normal play skips it.
static const bool pfOn=GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",0,0)!=0;
struct PerfScope{int s;LARGE_INTEGER a;PerfScope(int x):s(x){if(!pfOn)return;traceEv(x*2);QueryPerformanceCounter(&a);}~PerfScope(){if(!pfOn)return;traceEv(s*2+1);LARGE_INTEGER b;QueryPerformanceCounter(&b);pfTotal[s]+=b.QuadPart-a.QuadPart;pfFrame+=b.QuadPart-a.QuadPart;}};
static std::unordered_map<void*,uint64_t> movieVersions;static std::unordered_map<void*,IDirect3DTexture9*> snapshots;static uint64_t captures,resets,compatibilityDraws;static IDirect3DTexture9* compatibilityTex;
static const int W=3840,H=2160;static const float SCALE=3.75f;
static IDirect3DPixelShader9* pixelShader;static IDirect3DTexture9* maskTex;static IDirect3DTexture9* sceneCopy;static IDirect3DSurface9* sceneCopySurface;static std::unordered_set<void*> hdMovies;static uint64_t movieUploads,filterDraws;
static IDirect3D9* api;static IDirect3DDevice9* dev;static IDirect3DSurface9* readback;static bool begun;static uint64_t calls,draws,skipped,uploads,frames;static HRESULT lastError;
struct Tex{void* desc;void* data;int w,h,fmt;uint64_t lastFrame;uint64_t version;IDirect3DTexture9* tex;IDirect3DTexture9* uv;};static IDirect3DTexture9* boundUV;static std::vector<Tex> textures;
static int iv(void* p,int o){return *(int*)((char*)p+o);}static void* pv(void* p,int o){return *(void**)((char*)p+o);}
struct Hi {int w=0,h=0;uint64_t version=0;std::vector<uint32_t> data;};
struct Dim{int w,h;};static std::unordered_map<void*,Hi> high;static std::unordered_map<void*,Dim> dimensions;static uint64_t glyphs,copies,serial=1;static uint64_t highUploads,presents;static HRESULT presentResult;static uint64_t glyphCalls,glyphNullMetrics,glyphQueryFailed,glyphEmpty,glyphInvalidDimensions;
#include <psapi.h>
#include "hires_art.inc"
#include "profiler.inc"
#pragma comment(lib,"winmm.lib")
// Native-renderer test runs (no N2HD_Present): the profiler is driven from the original frame blit instead.
extern "C" void __cdecl N2HD_TestNativeFrame(double ms){Guard guard;if(!artIndexLoaded)artLoadIndex();if(!pfFreq){LARGE_INTEGER q;QueryPerformanceFrequency(&q);pfFreq=q.QuadPart;}double load=pfFreq?artLoadFrame*1000.0/pfFreq:0;
 static LARGE_INTEGER natPrev;LARGE_INTEGER nq;QueryPerformanceCounter(&nq);if(ms>150&&natPrev.QuadPart)artTraceDump(natPrev.QuadPart,nq.QuadPart,(double)pfFreq);natPrev=nq;
 if(ms>80&&artLog){fprintf(artLog,"longframe %.0fms our=0 engine_load=%.0f decoding=0 upload=0.0 frame=0\n",ms,load);fflush(artLog);}artLoadFrame=0;}
extern "C" void __cdecl N2HD_TestTick(){static wchar_t dir[MAX_PATH];static int ok=-1;if(ok<0)ok=GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",dir,MAX_PATH)?1:0;if(ok)profTick(dir,GetTickCount());}
extern "C" __declspec(dllexport) void __cdecl N2HD_RecordTexture(void* t){Guard guard;PerfScope perf(PF_LOAD);if(!t)return;void* data=pv(t,0x28);if(!data)return;VideoStop(data);hdMovies.erase(t);movieVersions.erase(data);auto snap=snapshots.find(t);if(snap!=snapshots.end()){snap->second->Release();snapshots.erase(snap);}for(auto it=textures.begin();it!=textures.end();){if(it->desc==t){if(it->uv)it->uv->Release();it->tex->Release();it=textures.erase(it);}else ++it;}dimensions[data]={iv(t,8),iv(t,12)};high.erase(data);art.erase(data);}
extern "C" __declspec(dllexport) void __cdecl N2HD_Glyph(void* font,GLYPHMETRICS* gm,void* native,int width,unsigned code){Guard guard;PerfScope perf(PF_GLYPH);
 ++glyphCalls;if(!font||!native||code==0x20||code==0x8140||code>0xffff)return;
 GLYPHMETRICS queried={};if(!gm){++glyphNullMetrics;MAT2 identity={};identity.eM11.value=1;identity.eM22.value=1;if(GetGlyphOutlineA(*(HDC*)0x629864,code,GGO_GRAY8_BITMAP,&queried,0,0,&identity)==GDI_ERROR){++glyphQueryFailed;return;}gm=&queried;}
 HDC dc=*(HDC*)0x629864;MAT2 mat={};mat.eM11.value=4;mat.eM22.value=4;GLYPHMETRICS big={};DWORD size=GetGlyphOutlineA(dc,code,GGO_GRAY8_BITMAP,&big,0,0,&mat);if(size==GDI_ERROR||size>4*1024*1024){++glyphQueryFailed;return;}if(!size){++glyphEmpty;return;}std::vector<unsigned char> buf(size);if(GetGlyphOutlineA(dc,code,GGO_GRAY8_BITMAP,&big,size,buf.data(),&mat)==GDI_ERROR)return;
 int height=(int)gm->gmBlackBoxY;auto dim=dimensions.find(native);if(dim!=dimensions.end()){width=dim->second.w;height=dim->second.h;}if(width<1||height<1||width>512||height>512){++glyphInvalidDimensions;return;}
 Hi h;h.w=width*4;h.h=height*4;h.version=++serial;h.data.assign(h.w*h.h,0);int dx=big.gmptGlyphOrigin.x-gm->gmptGlyphOrigin.x*4,dy=gm->gmptGlyphOrigin.y*4-big.gmptGlyphOrigin.y;uint32_t color=iv(font,12)&0xffffff;int pitch=(big.gmBlackBoxX+3)&~3;
 for(unsigned y=0;y<big.gmBlackBoxY;++y)for(unsigned x=0;x<big.gmBlackBoxX;++x){int tx=dx+x,ty=dy+y;if(tx<0||tx>=h.w||ty<0||ty>=h.h)continue;unsigned a=(buf[y*pitch+x]*255+32)/64;if(a)h.data[ty*h.w+tx]=color|(std::min(a,255U)<<24);}
 high[native]=std::move(h);++glyphs;
}
static void copyInto(Hi& d,const uint32_t* sd,int sw,int sh,int ox,int oy,uint32_t color,bool overwrite){
 for(int yy=std::max(0,-oy);yy<sh&&oy+yy<d.h;++yy)for(int xx=std::max(0,-ox);xx<sw&&ox+xx<d.w;++xx){uint32_t p=sd[yy*sw+xx];if(overwrite||(p>>24))d.data[(oy+yy)*d.w+ox+xx]=(p&0xff000000)|(color&0xffffff);}}
// Outline (AROUND) text: the engine copies each glyph twice to the same spot, into the text layer and, in a darker colour,
// into an outline layer that it draws at 8 offsets of 2 px. At 4x those offsets leave gaps beside the 5-6 px strokes and the
// outline showed as separate ghost copies (user 10-27). The darker copy of such a pair is widened by 2 px (4x, a disc), which
// closes the 8 copies up as at 1x. N2HD_TEST_OUTLINE_THIN=1 leaves it thin.
static void widen(const Hi& s,std::vector<uint32_t>& out){out.assign(s.data.size(),0);
 for(int y=0;y<s.h;++y)for(int x=0;x<s.w;++x){uint32_t m=0;for(int dy=-2;dy<=2;++dy)for(int dx=-2;dx<=2;++dx){if(dx*dx+dy*dy>4)continue;int sx=x+dx,sy=y+dy;if(sx<0||sy<0||sx>=s.w||sy>=s.h)continue;uint32_t a=s.data[sy*s.w+sx]>>24;if(a>m)m=a;}out[y*s.w+x]=m<<24;}}
static void copyGlyph(void* dst,void* src,int x,int y,uint32_t color,bool overwrite){
 if(!dst||!src)return;auto source=high.find(pv(src,0x28));if(source==high.end())return;void* key=pv(dst,0x28);int nw=iv(dst,8),nh=iv(dst,12);if(!key||nw<1||nh<1||nw>4096||nh>4096)return;
 if(high.find(key)==high.end()){Hi h;h.w=nw*4;h.h=nh*4;h.version=++serial;h.data.assign(h.w*h.h,0);uint32_t** rows=(uint32_t**)pv(dst,0x2c);for(int yy=0;yy<h.h;++yy)for(int xx=0;xx<h.w;++xx)h.data[yy*h.w+xx]=rows[yy/4][xx/4];high.emplace(key,std::move(h));}
 source=high.find(pv(src,0x28));Hi &s=source->second,&d=high.find(key)->second;int ox=x*4,oy=y*4;
 static struct{void* src;void* dst;int x,y;uint32_t color;bool overwrite;} last={};static int thin=-1;if(thin<0)thin=GetEnvironmentVariableA("N2HD_TEST_OUTLINE_THIN",0,0)?1:0;
 void* skey=pv(src,0x28);bool pair=!thin&&skey==last.src&&x==last.x&&y==last.y&&key!=last.dst&&((color^last.color)&0xffffff)&&s.w*s.h<=512*512;
 auto luma=[](uint32_t c){return ((c>>16)&255)*3+((c>>8)&255)*6+(c&255);};static std::vector<uint32_t> wide;
 if(pair&&luma(color)<luma(last.color)){widen(s,wide);copyInto(d,wide.data(),s.w,s.h,ox,oy,color,overwrite);}
 else{copyInto(d,s.data.data(),s.w,s.h,ox,oy,color,overwrite);
  if(pair){auto pd=high.find(last.dst);if(pd!=high.end()){widen(s,wide);copyInto(pd->second,wide.data(),s.w,s.h,last.x*4,last.y*4,last.color,last.overwrite);pd->second.version=++serial;}}}
 last={skey,key,x,y,color,overwrite};
 d.version=++serial;++copies;
}
extern "C" __declspec(dllexport) void __cdecl N2HD_CopyGlyph(void* dst,void* src,int x,int y,uint32_t c){Guard guard;PerfScope perf(PF_COPY);copyGlyph(dst,src,x,y,c,false);}
extern "C" __declspec(dllexport) void __cdecl N2HD_CopyGlyphMain(void* dst,void* src,int x,int y,uint32_t c){Guard guard;PerfScope perf(PF_COPY);copyGlyph(dst,src,x,y,c,true);}
extern "C" __declspec(dllexport) void __cdecl N2HD_Movie(void* movie){Guard guard;PerfScope perf(PF_MOVIE);if(!movie)return;void* o=pv(movie,0x6c);if(!o)return;void* t=pv(o,0x2c);if(t)VideoBind(pv(t,0x28));if(t&&iv(t,8)==3840&&iv(t,12)==2160)hdMovies.insert(t);}
static const char* shaderSource=R"SHADER(
sampler2D sourceTex : register(s0);
sampler2D sceneTex : register(s1);
sampler2D transitionTex : register(s2);
sampler2D videoUV : register(s3);
float4 flags : register(c0);
float4 main(float2 uv:TEXCOORD0,float2 screen:TEXCOORD1,float4 tint:COLOR0):COLOR0 {
 float4 c=tex2D(sourceTex,uv);if(flags.z>0.5){float y=(c.r-16.0/255.0)*1.16438356;float2 chroma=tex2D(videoUV,uv).ra-128.0/255.0;c=float4(y+1.596027*chroma.y,y-0.391762*chroma.x-0.812968*chroma.y,y+2.017232*chroma.x,1);}c.a*=tint.a;
 if(flags.x>0.5)c.a*=tex2D(transitionTex,screen).r;
 if(flags.y>3.5&&flags.y<4.5){float3 d=tex2D(sceneTex,screen).rgb;c.rgb=lerp(2*c.rgb*d,1-2*(1-c.rgb)*(1-d),step(0.5,d));}
 if(flags.y>4.5&&flags.y<5.5)c.rgb*=c.a;
 return c;
}
)SHADER";
static void releaseGpu(){Backlog::release();artRelease();
 VideoReset();boundUV=0;
 if(dev){dev->SetTexture(0,0);dev->SetTexture(1,0);dev->SetTexture(2,0);dev->SetTexture(3,0);dev->SetPixelShader(0);}
 for(auto &t:textures){t.tex->Release();if(t.uv)t.uv->Release();}textures.clear();for(auto &s:snapshots)s.second->Release();snapshots.clear();
 if(compatibilityTex){compatibilityTex->Release();compatibilityTex=0;}if(maskTex){maskTex->Release();maskTex=0;}if(sceneCopySurface){sceneCopySurface->Release();sceneCopySurface=0;}if(sceneCopy){sceneCopy->Release();sceneCopy=0;}if(pixelShader){pixelShader->Release();pixelShader=0;}if(readback){readback->Release();readback=0;}
 begun=false;
}
static bool ensure(){if(dev){HRESULT hr=dev->TestCooperativeLevel();if(hr==D3D_OK)return true;if(hr!=D3DERR_DEVICENOTRESET)return false;}HWND hwnd=*(HWND*)0x629854;if(!hwnd)return false;if(!api)api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return false;D3DPRESENT_PARAMETERS pp={};pp.BackBufferWidth=W;pp.BackBufferHeight=H;pp.BackBufferFormat=D3DFMT_X8R8G8B8;pp.BackBufferCount=1;pp.SwapEffect=D3DSWAPEFFECT_COPY;pp.hDeviceWindow=hwnd;pp.Windowed=TRUE;pp.PresentationInterval=D3DPRESENT_INTERVAL_IMMEDIATE;
 if(dev){releaseGpu();lastError=dev->Reset(&pp);if(SUCCEEDED(lastError))++resets;}else lastError=api->CreateDevice(D3DADAPTER_DEFAULT,D3DDEVTYPE_HAL,hwnd,D3DCREATE_SOFTWARE_VERTEXPROCESSING|D3DCREATE_MULTITHREADED,&pp,&dev);if(FAILED(lastError))return false;
 dev->SetRenderState(D3DRS_ZENABLE,FALSE);dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);dev->SetRenderState(D3DRS_LIGHTING,FALSE);dev->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);dev->SetRenderState(D3DRS_SCISSORTESTENABLE,TRUE);
 dev->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);dev->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);dev->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_MODULATE);dev->SetTextureStageState(0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);dev->SetTextureStageState(0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE);
 dev->SetSamplerState(0,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);dev->SetSamplerState(0,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);dev->SetSamplerState(0,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);dev->SetSamplerState(0,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);dev->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX2);
 ID3DBlob* code=0;ID3DBlob* errors=0;lastError=D3DCompile(shaderSource,strlen(shaderSource),"n2hd",0,0,"main","ps_2_0",D3DCOMPILE_OPTIMIZATION_LEVEL3,0,&code,&errors);if(errors)errors->Release();if(SUCCEEDED(lastError)){lastError=dev->CreatePixelShader((const DWORD*)code->GetBufferPointer(),&pixelShader);code->Release();}if(FAILED(lastError)){releaseGpu();dev->Release();dev=0;return false;}
 for(int sampler=1;sampler<=3;++sampler){dev->SetSamplerState(sampler,D3DSAMP_MINFILTER,D3DTEXF_LINEAR);dev->SetSamplerState(sampler,D3DSAMP_MAGFILTER,D3DTEXF_LINEAR);dev->SetSamplerState(sampler,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);dev->SetSamplerState(sampler,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);}dev->Clear(0,0,D3DCLEAR_TARGET,0,1,0);return true;}
extern "C" __declspec(dllexport) void __cdecl N2HD_PrepareMovie(const char* name){Guard guard;if(ensure())VideoPrepare(name,dev);}
static void begin(){if(ensure()&&!begun){lastError=dev->BeginScene();begun=SUCCEEDED(lastError);}}
extern "C" __declspec(dllexport) int __cdecl N2HD_Init(){Guard guard;return 1;}
extern "C" __declspec(dllexport) void __cdecl N2HD_Clear(){Guard guard;PerfScope perf(PF_CLEAR);if(ensure()){
 // The original CPU buffer is scratch; Present copies only the dirty rectangle.
 // The GPU target persists between frames, so clearing it entirely erases rows
 // outside the next redraw (especially earlier rows in a multiline text reveal).
 int* d=(int*)0x62949c;
 D3DRECT r={(LONG)(std::max(0,d[0])*SCALE),(LONG)(std::max(0,d[1])*SCALE),
            (LONG)(std::min(1024,d[2])*SCALE),(LONG)(std::min(576,d[3]+1)*SCALE)};
 if(r.x2>r.x1&&r.y2>r.y1)lastError=dev->Clear(1,&r,D3DCLEAR_TARGET,0,1,0);
}}
extern "C" __declspec(dllexport) void __cdecl N2HD_MovieFrame(void* data){Guard guard;PerfScope perf(PF_MOVIE);if(data)movieVersions[data]=++serial;}
static IDirect3DTexture9* upload(void* t){boundUV=0;auto sn=snapshots.find(t);if(sn!=snapshots.end())return sn->second;if(IDirect3DTexture9* hiresArt=artTexture(t))return hiresArt;int w=iv(t,8),h=iv(t,12),fmt=*(unsigned short*)((char*)t+4);void* data=pv(t,0x28);auto video=VideoFrame(data);auto hi=high.find(data);Hi* hsrc=hi==high.end()?0:&hi->second;auto mv=movieVersions.find(data);uint64_t version=video?video->serial:(hsrc?hsrc->version:(mv==movieVersions.end()?0:mv->second));if(video){w=video->w;h=video->h;fmt|=0x200;}else if(hsrc){w=hsrc->w;h=hsrc->h;fmt|=0x100;}if(w<1||h<1||w>16384||h>16384)return 0;
 Tex* found=0;for(auto &x:textures)if(x.desc==t&&x.data==data&&x.w==w&&x.h==h&&x.fmt==fmt){found=&x;break;}bool dynamic=!video&&mv==movieVersions.end()&&(pv(t,0)==0||(fmt&0x1000)!=0||((fmt&0xff)==0x16));
 if(found&&((!dynamic&&found->version==version)||(found->lastFrame==frames&&found->version==version))){found->lastFrame=frames;boundUV=found->uv;return found->tex;}
 int tw=fmt==5?1:w,th=fmt==5?1:h;if(!found){IDirect3DTexture9* tx=0;IDirect3DTexture9* uv=0;lastError=dev->CreateTexture(tw,th,1,D3DUSAGE_DYNAMIC,video?D3DFMT_L8:D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&tx,0);if(FAILED(lastError))return 0;if(video){lastError=dev->CreateTexture(w/2,h/2,1,D3DUSAGE_DYNAMIC,D3DFMT_A8L8,D3DPOOL_DEFAULT,&uv,0);if(FAILED(lastError)){tx->Release();return 0;}}textures.push_back({t,data,w,h,fmt,~0ULL,0,tx,uv});found=&textures.back();}
 D3DLOCKED_RECT lock;lastError=found->tex->LockRect(0,&lock,0,D3DLOCK_DISCARD);if(FAILED(lastError))return 0;uint32_t** rows=(uint32_t**)pv(t,0x2c);for(int y=0;y<th;++y){unsigned char* dst=(unsigned char*)lock.pBits+y*lock.Pitch;if(video)memcpy(dst,video->nv12.data()+size_t(y)*w,w);else{uint32_t* src=hsrc?hsrc->data.data()+y*w:rows[y];if((fmt&0x100)||((fmt&0xff)==0x16))memcpy(dst,src,tw*4);else for(int x=0;x<tw;++x)((uint32_t*)dst)[x]=src[x]|0xff000000;}}found->tex->UnlockRect(0);
 if(video){lastError=found->uv->LockRect(0,&lock,0,D3DLOCK_DISCARD);if(FAILED(lastError))return 0;for(int y=0;y<h/2;++y)memcpy((char*)lock.pBits+y*lock.Pitch,video->nv12.data()+size_t(h+y)*w,w);found->uv->UnlockRect(0);}found->lastFrame=frames;found->version=version;boundUV=found->uv;++uploads;if(hsrc)++highUploads;if((fmt&0xff)==0x16)++movieUploads;return found->tex;}
extern "C" __declspec(dllexport) void __cdecl N2HD_Capture(void* object,int* parameters){Guard guard;PerfScope perf(PF_CAPTURE);
 if(!object||!parameters||!*((unsigned char*)object+0x1c)||!ensure())return;void* t=pv(object,0x2c);if(!t)return;
 if(!parameters[2]&&(*(unsigned short*)((char*)t+4)&0x10))return;
 int tw=(int)(iv(t,8)*SCALE),th=(int)(iv(t,12)*SCALE),ox=(int)(iv(object,0x10)*SCALE),oy=(int)(iv(object,0x14)*SCALE);if(tw<=0||th<=0||tw>8192||th>8192)return;
 if(begun){dev->EndScene();begun=false;}
 auto it=snapshots.find(t);IDirect3DTexture9* dst=it==snapshots.end()?0:it->second;
 if(!dst){if(FAILED(dev->CreateTexture(tw,th,1,D3DUSAGE_RENDERTARGET,D3DFMT_X8R8G8B8,D3DPOOL_DEFAULT,&dst,0)))return;snapshots[t]=dst;}
 IDirect3DSurface9* src=0;IDirect3DSurface9* surface=0;dst->GetSurfaceLevel(0,&surface);dev->ColorFill(surface,0,0xff000000);
 RECT sr={std::max(0,ox),std::max(0,oy),std::min(W,ox+tw),std::min(H,oy+th)};RECT dr={sr.left-ox,sr.top-oy,sr.right-ox,sr.bottom-oy};
 if(sr.right>sr.left&&sr.bottom>sr.top&&SUCCEEDED(dev->GetBackBuffer(0,0,D3DBACKBUFFER_TYPE_MONO,&src))){lastError=dev->StretchRect(src,&sr,surface,&dr,D3DTEXF_NONE);if(SUCCEEDED(lastError))++captures;src->Release();}surface->Release();
}
struct V{float x,y,z,rhw;DWORD color;float u,v,s,t;};
// Row clip spans (+0xf0) are drawn on the GPU (N2HD_Draw); N2HD_TEST_SPAN_COMPAT=1 sends them down the 1x path as before.
static bool spanCompat(){static int v=-1;if(v<0)v=GetEnvironmentVariableA("N2HD_TEST_SPAN_COMPAT",0,0)?1:0;return v!=0;}
static bool needsCompatibility(void* o,void* arg,void* filter){if(arg)return true;void* m=pv(o,0x28);if(m&&pv(m,0xf0)&&spanCompat())return true;if(filter){int stride=iv(filter,0x20);if(!pv(filter,0x28)||stride<1024||stride>16384)return true;}return false;}
extern "C" __declspec(dllexport) void __cdecl N2HD_AfterDraw(void* object,void* arg,void* filter){Guard guard;PerfScope perf(PF_DRAW);
 if(!object||pv(object,0x30)||!*((unsigned char*)object+0x1c)||!needsCompatibility(object,arg,filter)||!ensure())return;void* bits=pv(object,0x18);void* transform=pv(object,0x28);int* clip=(int*)pv(object,0x24);if(!bits||!transform||!clip||*(int*)0x629494!=32)return;
 short* x=(short*)((char*)transform+0x80);short* y=(short*)((char*)transform+0x88);int* dirty=(int*)0x62949c;
 int l=std::max({0,dirty[0],clip[0]/4,(int)*std::min_element(x,x+4)}),t=std::max({0,dirty[1],clip[1],(int)*std::min_element(y,y+4)}),r=std::min({1024,dirty[2],(clip[0]+clip[2])/4,(int)*std::max_element(x,x+4)}),b=std::min({576,dirty[3]+1,clip[1]+clip[3],(int)*std::max_element(y,y+4)+1});if(r<=l||b<=t)return;
 if(!compatibilityTex&&FAILED(dev->CreateTexture(1024,576,1,D3DUSAGE_DYNAMIC,D3DFMT_X8R8G8B8,D3DPOOL_DEFAULT,&compatibilityTex,0)))return;D3DLOCKED_RECT lock;if(FAILED(compatibilityTex->LockRect(0,&lock,0,D3DLOCK_DISCARD)))return;for(int yy=0;yy<576;++yy)memcpy((char*)lock.pBits+yy*lock.Pitch,(char*)bits+yy*4096,4096);compatibilityTex->UnlockRect(0);begin();if(!begun)return;
 RECT rc={(LONG)(l*SCALE),(LONG)(t*SCALE),(LONG)(r*SCALE),(LONG)(b*SCALE)};V v[4]={{-.5f,-.5f,0,1,0xffffffff,0,0,0,0},{W-.5f,-.5f,0,1,0xffffffff,1,0,1,0},{W-.5f,H-.5f,0,1,0xffffffff,1,1,1,1},{-.5f,H-.5f,0,1,0xffffffff,0,1,0,1}};
 dev->SetPixelShader(pixelShader);float flags[4]={};dev->SetPixelShaderConstantF(0,flags,1);dev->SetTexture(0,compatibilityTex);dev->SetTexture(1,0);dev->SetTexture(2,0);dev->SetScissorRect(&rc);dev->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_ZERO);lastError=dev->DrawPrimitiveUP(D3DPT_TRIANGLEFAN,2,v,sizeof(V));if(SUCCEEDED(lastError))++compatibilityDraws;
}
extern "C" __declspec(dllexport) void __cdecl N2HD_Draw(void* object,void* arg2,void* filter){Guard guard;PerfScope perf(PF_DRAW);++calls;if(!object)return;int opacity=*((unsigned char*)object+0x1c);if(!opacity)return;if(pv(object,0x30)||needsCompatibility(object,arg2,filter)){++skipped;return;}begin();if(!begun)return;
 void* t=pv(object,0x2c);void* m=pv(object,0x28);int* clip=(int*)pv(object,0x24);if(!t||!m||!clip)return;int sw=iv(t,8),sh=iv(t,12);if(sw<1||sh<1)return;IDirect3DTexture9* tex=upload(t);if(!tex)return;
 short* sx=(short*)((char*)m+0x70),*sy=(short*)((char*)m+0x78),*x=(short*)((char*)m+0x80),*y=(short*)((char*)m+0x88);int* dirty=(int*)0x62949c;
 int mode=iv(object,0xc)&0xfff;
 if(mode==4){if(begun){dev->EndScene();begun=false;}if(!sceneCopy){lastError=dev->CreateTexture(W,H,1,D3DUSAGE_RENDERTARGET,D3DFMT_X8R8G8B8,D3DPOOL_DEFAULT,&sceneCopy,0);if(SUCCEEDED(lastError))sceneCopy->GetSurfaceLevel(0,&sceneCopySurface);}IDirect3DSurface9* current=0;if(sceneCopySurface&&SUCCEEDED(dev->GetBackBuffer(0,0,D3DBACKBUFFER_TYPE_MONO,&current))){lastError=dev->StretchRect(current,0,sceneCopySurface,0,D3DTEXF_NONE);current->Release();}begin();}
 if(filter){int stride=iv(filter,0x20);unsigned char* data=(unsigned char*)pv(filter,0x28);unsigned char* lut=(unsigned char*)filter+0x2c;if(!data||stride<1024||stride>16384){++skipped;return;}if(!maskTex)dev->CreateTexture(1024,576,1,D3DUSAGE_DYNAMIC,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&maskTex,0);if(!maskTex)return;D3DLOCKED_RECT l;if(FAILED(maskTex->LockRect(0,&l,0,D3DLOCK_DISCARD)))return;for(int yy=0;yy<576;++yy){uint32_t* row=(uint32_t*)((char*)l.pBits+yy*l.Pitch);for(int xx=0;xx<1024;++xx){unsigned v=lut[data[yy*stride+xx]];row[xx]=0xff000000|v*0x10101;}}maskTex->UnlockRect(0);++filterDraws;}
 dev->SetPixelShader(pixelShader);float flags[4]={filter?1.0f:0.0f,(float)mode,boundUV?1.0f:0.0f,0};dev->SetPixelShaderConstantF(0,flags,1);dev->SetTexture(1,mode==4?sceneCopy:0);dev->SetTexture(2,filter?maskTex:0);dev->SetTexture(3,boundUV);
 dev->SetRenderState(D3DRS_BLENDOP,mode==3?D3DBLENDOP_REVSUBTRACT:D3DBLENDOP_ADD);dev->SetRenderState(D3DRS_SRCBLEND,mode==5?D3DBLEND_DESTCOLOR:D3DBLEND_SRCALPHA);dev->SetRenderState(D3DRS_DESTBLEND,(mode==2||mode==3)?D3DBLEND_ONE:D3DBLEND_INVSRCALPHA);
 bool hdMovie=hdMovies.count(t)!=0;
 RECT rc;rc.left=std::max(0,(int)(std::max(dirty[0],clip[0]/4)*SCALE));rc.right=std::min(W,(int)(std::min(dirty[2],(clip[0]+clip[2])/4)*SCALE));rc.top=std::max(0,(int)(std::max(dirty[1],clip[1])*SCALE));rc.bottom=std::min(H,(int)(std::min(dirty[3]+1,clip[1]+clip[3])*SCALE));if(rc.right<=rc.left||rc.bottom<=rc.top)return;
 V v[4];int minU=*std::min_element(sx,sx+4),minV=*std::min_element(sy,sy+4);
 bool rectangle=x[0]==x[3]&&x[1]==x[2]&&y[0]==y[1]&&y[2]==y[3];int bottom=*std::max_element(y,y+4);
 for(int i=0;i<4;++i){float px=hdMovie?(x[i]-iv(object,0x10))+iv(object,0x10)*SCALE:x[i]*SCALE;float py=hdMovie?(y[i]-iv(object,0x14))+iv(object,0x14)*SCALE:y[i]*SCALE;if(rectangle&&y[i]==bottom)py+=hdMovie?1.0f:SCALE;v[i]={px-0.5f,py-0.5f,0,1,(DWORD)((opacity<<24)|0xffffff),(sx[i]+(sx[i]>minU?1.0f:0.0f))/sw,(sy[i]+(sy[i]>minV?1.0f:0.0f))/sh,px/W,py/H};}
 dev->SetTexture(0,tex);short* spans=(short*)pv(m,0xf0);
 if(!spans){dev->SetScissorRect(&rc);lastError=dev->DrawPrimitiveUP(D3DPT_TRIANGLEFAN,2,v,sizeof(V));if(SUCCEEDED(lastError))++draws;return;}
 // Row clip spans: 20-byte records indexed by screen row, [0] left and [2] right (exclusive). The engine rasterizer skips
 // a row when left > right or its row flag (+0x2df4) is 0, and starts at 0 for a negative left. Rows with the same span
 // share one scissor rectangle.
 int y0=std::max({0,dirty[1],clip[1],(int)*std::min_element(y,y+4)}),y1=std::min({576,dirty[3]+1,clip[1]+clip[3],(int)*std::max_element(y,y+4)+1});
 auto spanOf=[&](int row,int& sl,int& sr){short a=spans[row*10],b=spans[row*10+1];if(!*(int*)((char*)m+0x2df4+row*4)||a>b){sl=sr=0;return;}sl=std::max(0,(int)a);sr=std::max(0,(int)b);};
 for(int row=y0;row<y1;){int sl,sr;spanOf(row,sl,sr);int end=row+1;for(;end<y1;++end){int nl,nr;spanOf(end,nl,nr);if(nl!=sl||nr!=sr)break;}
  RECT sc={std::max(rc.left,(LONG)(sl*SCALE)),std::max(rc.top,(LONG)(row*SCALE)),std::min(rc.right,(LONG)(sr*SCALE)),std::min(rc.bottom,(LONG)(end*SCALE))};
  if(sc.right>sc.left&&sc.bottom>sc.top){dev->SetScissorRect(&sc);lastError=dev->DrawPrimitiveUP(D3DPT_TRIANGLEFAN,2,v,sizeof(V));if(SUCCEEDED(lastError))++draws;}
  row=end;}
}
#include "backlog_renderer.inc"
extern "C" __declspec(dllexport) void __cdecl N2HD_End(){Guard guard;PerfScope perf(PF_END);if(begun){dev->EndScene();begun=false;}++frames;artFrameEnd();if(frames%60==0){for(auto it=textures.begin();it!=textures.end();){if(frames-it->lastFrame>300){if(it->uv)it->uv->Release();it->tex->Release();it=textures.erase(it);}else ++it;}}}
extern "C" __declspec(dllexport) int __cdecl N2HD_Save(const wchar_t* path);
// Test runs only (Claude): N2HD_TEST_SHOT_MS=<ms> with N2HD_PROFILE_DIR saves the 4K target there every <ms> (at most 60).
static void testStat(DWORD now){static DWORD lastStat=0;if(!artLog||(lastStat&&now-lastStat<10000))return;lastStat=now;double f=pfFreq?1000.0/pfFreq:0;size_t freeAll=0,freeMax=0;{MEMORY_BASIC_INFORMATION mi;for(uint64_t a=0x10000;a<0xfffe0000ull;a+=mi.RegionSize){if(!VirtualQuery((void*)(uintptr_t)a,&mi,sizeof mi)||!mi.RegionSize)break;if(mi.State==MEM_FREE){freeAll+=mi.RegionSize;if(mi.RegionSize>freeMax)freeMax=mi.RegionSize;}}}PROCESS_MEMORY_COUNTERS_EX pmc{};pmc.cb=sizeof pmc;K32GetProcessMemoryInfo(GetCurrentProcess(),(PROCESS_MEMORY_COUNTERS*)&pmc,sizeof pmc);fprintf(artLog,"mem t=%lu free_mb=%u largest_free_mb=%u private_mb=%u pending_mb=%u cache_mb=%u\n",now,(unsigned)(freeAll>>20),(unsigned)(freeMax>>20),(unsigned)(pmc.PrivateUsage>>20),(unsigned)(artPendingBytes>>20),(unsigned)(artCacheBytes>>20));fprintf(artLog,"stat t=%lu presents=%llu draw=%.0f glyph=%.0f copy=%.0f capture=%.0f clear=%.0f end=%.0f present=%.0f movie=%.0f load=%.0f our_over16=%llu our_over50=%llu our_max=%.0f long50=%llu long100=%llu uploads=%llu late=%llu decode_ms_max=%llu upload_ms_max=%llu cache_mb=%llu hist<12/20/35/50/100/+=%llu/%llu/%llu/%llu/%llu/%llu engine_load=%.0f engine_load_max=%.0f long_with_load=%llu\n",now,(unsigned long long)presents,pfTotal[PF_DRAW]*f,pfTotal[PF_GLYPH]*f,pfTotal[PF_COPY]*f,pfTotal[PF_CAPTURE]*f,pfTotal[PF_CLEAR]*f,pfTotal[PF_END]*f,pfTotal[PF_PRESENT]*f,pfTotal[PF_MOVIE]*f,pfTotal[PF_LOAD]*f,(unsigned long long)pfOver16,(unsigned long long)pfOver50,pfFrameMax*f,(unsigned long long)artLongFrames50,(unsigned long long)artLongFrames100,(unsigned long long)artUploads,(unsigned long long)artLate,(unsigned long long)artDecodeMsMax,(unsigned long long)artUploadMsMax,(unsigned long long)(artCacheBytes>>20),(unsigned long long)artFrameHist[0],(unsigned long long)artFrameHist[1],(unsigned long long)artFrameHist[2],(unsigned long long)artFrameHist[3],(unsigned long long)artFrameHist[4],(unsigned long long)artFrameHist[5],artLoadTotal*f,artLoadMax*f,(unsigned long long)artLongWithLoad);fflush(artLog);}
static void testShot(){static int every=-1,shots=0;static DWORD last=0;static bool test=false;static wchar_t dir[MAX_PATH];if(every<0){wchar_t v[32];every=GetEnvironmentVariableW(L"N2HD_TEST_SHOT_MS",v,32)?_wtoi(v):0;test=GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",dir,MAX_PATH)!=0;if(!test)every=0;}DWORD now=GetTickCount();if(test){testStat(now);profTick(dir,now);}if(every<=0||shots>=60)return;if(last&&now-last<(DWORD)every)return;last=now;wchar_t p[MAX_PATH];wsprintfW(p,L"%s\\shot-%03d.bmp",dir,shots++);N2HD_Save(p);if(artLog){fprintf(artLog,"shot %d t=%lu presents=%llu loads=%llu matched=%llu uploads=%llu fails=%llu stale=%llu decode_ms_max=%llu upload_ms_max=%llu late=%llu cache_mb=%llu long50=%llu long100=%llu\n",shots-1,now,(unsigned long long)presents,(unsigned long long)artLoads,(unsigned long long)artMatched,(unsigned long long)artUploads,(unsigned long long)artFails,(unsigned long long)artStale,(unsigned long long)artDecodeMsMax,(unsigned long long)artUploadMsMax,(unsigned long long)artLate,(unsigned long long)(artCacheBytes>>20),(unsigned long long)artLongFrames50,(unsigned long long)artLongFrames100);fflush(artLog);}}
extern "C" __declspec(dllexport) int __cdecl N2HD_Present(){Guard guard;PerfScope perf(PF_PRESENT);if(dev&&SUCCEEDED(lastError)){presentResult=dev->Present(0,0,0,0);if(SUCCEEDED(presentResult)){++presents;artFrameTiming();testShot();return 1;}}return 0;}
extern "C" __declspec(dllexport) int __cdecl N2HD_Save(const wchar_t* path){Guard guard;if(!dev)return 0;if(begun){dev->EndScene();begun=false;}IDirect3DSurface9* src=0;lastError=dev->GetBackBuffer(0,0,D3DBACKBUFFER_TYPE_MONO,&src);if(FAILED(lastError))return 0;if(!readback)lastError=dev->CreateOffscreenPlainSurface(W,H,D3DFMT_X8R8G8B8,D3DPOOL_SYSTEMMEM,&readback,0);if(FAILED(lastError)){src->Release();return 0;}lastError=dev->GetRenderTargetData(src,readback);src->Release();if(FAILED(lastError))return 0;D3DLOCKED_RECT lock;lastError=readback->LockRect(&lock,0,D3DLOCK_READONLY);if(FAILED(lastError))return 0;
 HANDLE f=CreateFileW(path,GENERIC_WRITE,FILE_SHARE_READ,0,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,0);if(f==INVALID_HANDLE_VALUE){readback->UnlockRect();return 0;}BITMAPFILEHEADER bf={};BITMAPINFOHEADER bi={};bf.bfType=0x4d42;bf.bfSize=54+W*H*4;bf.bfOffBits=54;bi.biSize=40;bi.biWidth=W;bi.biHeight=-H;bi.biPlanes=1;bi.biBitCount=32;bi.biSizeImage=W*H*4;DWORD n;BOOL ok=WriteFile(f,&bf,14,&n,0)&&WriteFile(f,&bi,40,&n,0);for(int y=0;y<H&&ok;++y)ok=WriteFile(f,(char*)lock.pBits+y*lock.Pitch,W*4,&n,0);CloseHandle(f);readback->UnlockRect();return ok;}
extern "C" __declspec(dllexport) void __cdecl N2HD_Stats(uint64_t* out){Guard guard;out[0]=calls;out[1]=draws;out[2]=skipped;out[3]=uploads;out[4]=(uint32_t)lastError;out[5]=frames;out[6]=textures.size();out[7]=glyphs;out[8]=copies;out[9]=high.size();out[10]=glyphCalls;out[11]=glyphNullMetrics;out[12]=glyphQueryFailed;out[13]=glyphEmpty;out[14]=glyphInvalidDimensions;out[15]=highUploads;out[16]=presents;out[17]=(uint32_t)presentResult;out[18]=movieUploads;out[19]=hdMovies.size();out[20]=filterDraws;out[21]=captures;out[22]=resets;out[23]=compatibilityDraws;}
BOOL WINAPI DllMain(HINSTANCE h,DWORD why,LPVOID){if(why==DLL_PROCESS_ATTACH){InitializeCriticalSection(&rendererLock);DisableThreadLibraryCalls(h);}return TRUE;}
