// Codex 2026-11-02: reuse Windows' PNG decoder for the exact native pixel layout.
// Unknown PNG features retain the original decoder. The EXE/file-structure layout
// is protected by runtime_hooks.cpp's SHA-256 and hook-byte checks.
#include <wincodec.h>
#pragma comment(lib,"windowscodecs.lib")
namespace FastPng {
static unsigned be32(const unsigned char* p){return ((unsigned)p[0]<<24)|((unsigned)p[1]<<16)|((unsigned)p[2]<<8)|p[3];}
static int mode(){static int m=[](){char v[16];return GetEnvironmentVariableA("N2HD_FAST_PNG",v,16)?atoi(v):1;}();return m;}
static bool eligible(const unsigned char* b,size_t n,unsigned& w,unsigned& h,unsigned& type){
 static const unsigned char sig[]={137,80,78,71,13,10,26,10};
 if(!b||n<33||n>128u*1024*1024||memcmp(b,sig,8)||be32(b+8)!=13||memcmp(b+12,"IHDR",4))return false;
 w=be32(b+16);h=be32(b+20);type=b[25];
 if(!w||!h||w>8192||h>8192||(w&1)||b[24]!=8||(type!=2&&type!=6)||b[26]||b[27]||b[28]||uint64_t(w)*4*(h+2)>64u*1024*1024)return false;
 // The native decoder applies gAMA. Leave gamma, palette, transparency-key,
 // interlaced and odd-width paths with that decoder rather than changing pixels.
 bool end=false;
 for(size_t p=8;p+12<=n;){unsigned z=be32(b+p);if(z>n-p-12)return false;const unsigned char* k=b+p+4;
  if(!memcmp(k,"gAMA",4)||!memcmp(k,"tRNS",4)||!memcmp(k,"acTL",4))return false;
  if(!memcmp(k,"IEND",4)){end=z==0&&p+12==n;break;}p+=size_t(z)+12;}
 return end;
}
static bool decode(void* t,void* file){
 if(!t||!file)return false;const unsigned char* bytes=*(unsigned char**)((char*)file+0x11c);unsigned size=*(unsigned*)((char*)file+0x108),w=0,h=0,type=0;
 if(!eligible(bytes,size,w,h,type))return false;
 HRESULT init=CoInitializeEx(0,COINIT_MULTITHREADED);if(FAILED(init)&&init!=RPC_E_CHANGED_MODE)return false;
 IWICImagingFactory* factory=0;IWICStream* stream=0;IWICBitmapDecoder* decoder=0;IWICBitmapFrameDecode* frame=0;IWICFormatConverter* convert=0;void* buf=0;bool ok=false;
 do{
  if(FAILED(CoCreateInstance(CLSID_WICImagingFactory,0,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&factory))))break;
  if(FAILED(factory->CreateStream(&stream))||FAILED(stream->InitializeFromMemory((BYTE*)bytes,size)))break;
  if(FAILED(CoCreateInstance(CLSID_WICPngDecoder,0,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&decoder)))||FAILED(decoder->Initialize(stream,WICDecodeMetadataCacheOnLoad)))break;
  if(FAILED(decoder->GetFrame(0,&frame)))break;UINT fw=0,fh=0;if(FAILED(frame->GetSize(&fw,&fh))||fw!=w||fh!=h)break;
  if(FAILED(factory->CreateFormatConverter(&convert))||FAILED(convert->Initialize(frame,GUID_WICPixelFormat32bppBGRA,WICBitmapDitherTypeNone,0,0,WICBitmapPaletteTypeCustom)))break;
  const size_t nativeBytes=((size_t(w)*4*(h+2)+0x43f)&~size_t(0x3f))+0x40;
  buf=HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,nativeBytes);if(!buf)break;
  if(FAILED(convert->CopyPixels(0,w*4,w*4*h,(BYTE*)buf)))break;
  *(unsigned short*)((char*)t+4)=type==6?0x101:7;
  for(int o:{8,0x10})*(unsigned*)((char*)t+o)=w;
  for(int o:{0xc,0x14})*(unsigned*)((char*)t+o)=h;
  *(void**)((char*)t+0x28)=buf;buf=0;ok=true;
 }while(false);
 if(buf)HeapFree(GetProcessHeap(),0,buf);
 if(convert)convert->Release();if(frame)frame->Release();if(decoder)decoder->Release();if(stream)stream->Release();if(factory)factory->Release();
 if(SUCCEEDED(init))CoUninitialize();return ok;
}
static void compare(void* native,void* fast,double nativeMs,double fastMs){
 void* a=*(void**)((char*)native+0x28);void* b=*(void**)((char*)fast+0x28);
 size_t na=HeapSize(GetProcessHeap(),0,a),nb=HeapSize(GetProcessHeap(),0,b);bool same=na==nb&&na!=(size_t)-1&&!memcmp(a,b,na);
 for(int f:ImgCache::FIELDS)if(*(unsigned*)((char*)native+f)!=*(unsigned*)((char*)fast+f))same=false;
 char line[700];sprintf_s(line,"fastpng verify=%s native_ms=%.3f wic_ms=%.3f bytes=%u name=%s",same?"SAME":"DIFF",nativeMs,fastMs,(unsigned)nb,ImgCache::cur?ImgCache::cur:"?");ImgCache::log(line);
 HeapFree(GetProcessHeap(),0,b);
}
}
