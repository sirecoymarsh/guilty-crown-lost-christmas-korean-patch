// Backlog is drawn straight into the native framebuffer, bypassing text textures.
// Mirror that path at 4x and restore ruby by complete, boundary-checked paragraphs
// from the hash-bound reviewed registry. The native save/history format is untouched.
#include <string>
#include <map>
#include <set>
#include "backlog_ruby_map.h"
extern "C" int __cdecl N2HD_JumpHover(unsigned*,unsigned*);
namespace Backlog {
const int BW=4096,BH=2304;
struct Glyph {const unsigned short* record;unsigned code,color;int x,y,ascent,left,top,width,height,originalX,advance;};
struct Annotation {int unit,span;size_t start,length;std::wstring reading;};
struct Ink {int kind,unit,span,part,first,count;float x,y,w,h;};
struct Bitmap {int w=0,h=0,left=0,top=0;std::vector<unsigned char> alpha;};
static std::vector<Glyph> visible;
static std::vector<const unsigned short*> positions;
static std::vector<Annotation> annotations;
static std::vector<Ink> ink;
static std::vector<uint32_t> pixels;
static std::vector<unsigned char> nativeRuby,nativeRubySmall;
static std::unordered_map<unsigned,Bitmap> glyphCache;
static std::map<std::wstring,Bitmap> rubyCache;
static std::unordered_map<unsigned,int> advanceCache;
static LOGFONTW font={};static bool fontKnown=false;
static uint64_t historyHash=0,layoutHash=0,generation=0,errors=0;
static IDirect3DTexture9* texture=0;static bool uploadPending=false;
static uint64_t hash(uint64_t h,uint64_t x){return (h^x)*1099511628211ULL;}
static bool whitespace(unsigned c){return c==0x20||c==0xa1a1||c==0x8140;}
static bool newline(unsigned c){return c==9||c==10||c==13;}
static wchar_t decode(unsigned c){if(c<128)return (wchar_t)c;char s[2]={(char)(c>>8),(char)c};wchar_t w=0;if(MultiByteToWideChar(949,MB_ERR_INVALID_CHARS,s,2,&w,1)!=1)return 0;return w;}
// The native history puts every character, including ASCII spaces, in a 25px
// slot. Retain its rows/scroll/save records, but place glyphs by the same GDI
// font advances used by normal text. Apply the x coordinate to both renderers.
static int advance(HDC dc,unsigned code){
 auto found=advanceCache.find(code);if(found!=advanceCache.end())return found->second;
 wchar_t w=decode(code);SIZE size={};int cell=*(int*)0x583dc4;
 if(!w||!GetTextExtentPoint32W(dc,&w,1,&size)||size.cx<1||size.cx>128){++errors;return cell;}
 advanceCache[code]=size.cx;return size.cx;
}
static int naturalX(HDC dc,const unsigned short* record,int originalX){
 auto base=*(unsigned char**)0x62993c;if(!base)return originalX;
 auto start=(const unsigned short*)(base+0x28),end=*(const unsigned short**)(base+0x24);
 if(record<start||record>=end)return originalX;
 auto row=record;while(row>start&&row[-1]>=0x20)--row;
 if(record-row>256){++errors;return originalX;}
 int width=0;for(auto p=row;p<record;++p)width+=advance(dc,*p);
 return originalX-(int)(record-row)*(*(int*)0x583dc4)+width;
}
static void readHistory(){
 auto base=*(unsigned char**)0x62993c;if(!base)return;auto start=(unsigned short*)(base+0x28),end=*(unsigned short**)(base+0x24);
 if(end<start||end-start>0x200000){++errors;return;}uint64_t h=1469598103934665603ULL;
 for(auto p=start;p<end;++p)h=hash(h,*p);if(h==historyHash)return;historyHash=h;
 positions.clear();annotations.clear();std::wstring plain;bool voice=false;
 for(auto p=start;p<end;++p){unsigned c=*p;if(c==0x10){voice=!voice;continue;}if(voice||c<0x20||whitespace(c))continue;wchar_t w=decode(c);if(!w){++errors;w=0xfffd;}plain+=w;positions.push_back(p);}
 std::set<std::wstring> seen;
 for(const auto &u:rubyUnits){size_t len=wcslen(u.plain),at=0;if(!len)continue;while((at=plain.find(u.plain,at))!=std::wstring::npos){
  const unsigned short* a=positions[at];const unsigned short* b=positions[at+len-1]+1;
  while(a>start&&whitespace(a[-1]))--a;while(b<end&&whitespace(*b))++b;
  bool boundaries=(a==start||newline(a[-1])||a[-1]==0x10)&&(b==end||newline(*b)||*b==0x10);
  if(boundaries)for(int j=0;j<u.count;++j){const auto &s=u.spans[j];if(s.start<0||s.length<1||s.start+s.length>(int)len){++errors;continue;}
   std::wstring key=std::to_wstring(at+s.start)+L":"+std::to_wstring(s.length)+L":"+s.reading;
   if(seen.insert(key).second)annotations.push_back({u.id,j,at+s.start,(size_t)s.length,s.reading});}
  at+=len;
 }}
}
static Bitmap glyph(HDC dc,unsigned code){
 Bitmap b;MAT2 m={};m.eM11.value=4;m.eM22.value=4;GLYPHMETRICS g={};
 DWORD n=GetGlyphOutlineW(dc,decode(code),GGO_GRAY8_BITMAP,&g,0,0,&m);
 if(n==GDI_ERROR||n>1024*1024){++errors;return b;}if(!n)return b;
 std::vector<unsigned char> raw(n);if(GetGlyphOutlineW(dc,decode(code),GGO_GRAY8_BITMAP,&g,n,raw.data(),&m)==GDI_ERROR){++errors;return b;}
 b.w=g.gmBlackBoxX;b.h=g.gmBlackBoxY;b.left=g.gmptGlyphOrigin.x;b.top=g.gmptGlyphOrigin.y;b.alpha.resize(b.w*b.h);int pitch=(b.w+3)&~3;
 for(int y=0;y<b.h;++y)for(int x=0;x<b.w;++x)b.alpha[y*b.w+x]=(unsigned char)std::min(255U,(raw[y*pitch+x]*255U+32)/64);return b;
}
static Bitmap reading(const std::wstring& s){
 auto it=rubyCache.find(s);if(it!=rubyCache.end())return it->second;
 Bitmap b;HDC dc=CreateCompatibleDC(0);LOGFONTW lf=font;lf.lfHeight=52;lf.lfWidth=0;lf.lfQuality=ANTIALIASED_QUALITY;
 HFONT f=CreateFontIndirectW(&lf);HGDIOBJ old=SelectObject(dc,f);SIZE z={};GetTextExtentPoint32W(dc,s.data(),(int)s.size(),&z);
 int w=z.cx+16,h=80;if(w<1||w>4096){++errors;SelectObject(dc,old);DeleteObject(f);DeleteDC(dc);return b;}
 BITMAPINFO bi={};bi.bmiHeader.biSize=40;bi.bmiHeader.biWidth=w;bi.bmiHeader.biHeight=-h;bi.bmiHeader.biPlanes=1;bi.bmiHeader.biBitCount=32;
 void* bits=0;HBITMAP dib=CreateDIBSection(dc,&bi,DIB_RGB_COLORS,&bits,0,0);HGDIOBJ oldBmp=SelectObject(dc,dib);memset(bits,0,w*h*4);SetBkColor(dc,RGB(0,0,0));SetTextColor(dc,RGB(255,255,255));TextOutW(dc,8,0,s.data(),(int)s.size());GdiFlush();
 auto p=(uint32_t*)bits;int l=w,t=h,r=0,bt=0;for(int y=0;y<h;++y)for(int x=0;x<w;++x)if(p[y*w+x]&0xffffff){l=std::min(l,x);t=std::min(t,y);r=std::max(r,x+1);bt=std::max(bt,y+1);}
 if(r>l&&bt>t){b.w=r-l;b.h=bt-t;b.alpha.resize(b.w*b.h);for(int y=0;y<b.h;++y)for(int x=0;x<b.w;++x)b.alpha[y*b.w+x]=(unsigned char)p[(t+y)*w+l+x];}
 SelectObject(dc,oldBmp);DeleteObject(dib);SelectObject(dc,old);DeleteObject(f);DeleteDC(dc);rubyCache[s]=b;return b;
}
static void paint(const Bitmap& b,int x,int y,unsigned color,bool ruby){
 for(int yy=0;yy<b.h;++yy)for(int xx=0;xx<b.w;++xx){int dx=x+xx,dy=y+yy;unsigned a=b.alpha[yy*b.w+xx];if(!a)continue;if(dx<0||dx>=BW||dy<0||dy>=BH){++errors;continue;}uint32_t &p=pixels[dy*BW+dx];unsigned old=p>>24;unsigned alpha=a+(old*(255-a)+127)/255;p=(alpha<<24)|(color&0xffffff);if(ruby)nativeRuby[dy*BW+dx]=(unsigned char)std::max(a,(unsigned)nativeRuby[dy*BW+dx]);}
}
static void rebuild(){
 pixels.assign(BW*BH,0);nativeRuby.assign(BW*BH,0);ink.clear();HDC dc=CreateCompatibleDC(0);HFONT f=CreateFontIndirectW(&font);HGDIOBJ old=SelectObject(dc,f);
 std::unordered_map<const unsigned short*,size_t> byRecord;
 for(size_t i=0;i<visible.size();++i){auto &g=visible[i];byRecord[g.record]=i;auto it=glyphCache.find(g.code);if(it==glyphCache.end())it=glyphCache.emplace(g.code,glyph(dc,g.code)).first;const Bitmap &b=it->second;int x=g.x*4+b.left,y=(g.y+g.ascent)*4-b.top;paint(b,x,y,g.color,false);ink.push_back({0,0,0,0,0,0,x/4.f,y/4.f,b.w/4.f,b.h/4.f});}
 SelectObject(dc,old);DeleteObject(f);DeleteDC(dc);
 unsigned jumpLo=0,jumpHi=0;
 if(N2HD_JumpHover(&jumpLo,&jumpHi)){
  auto hb=*(unsigned char**)0x62993c;auto first=(const unsigned short*)(hb+0x28);
  std::map<int,std::pair<int,int>> rows;
  for(const auto& g:visible){unsigned off=(unsigned)(g.record-first);if(off<jumpLo||off>=jumpHi)continue;auto i=rows.find(g.y);if(i==rows.end())rows[g.y]={g.x,g.x+g.advance};else{ i->second.first=std::min(i->second.first,g.x);i->second.second=std::max(i->second.second,g.x+g.advance);}}
  for(const auto& row:rows){Bitmap b;b.w=(row.second.second-row.second.first)*4;b.h=3;b.alpha.assign(b.w*b.h,190);paint(b,row.second.first*4,(row.first+25)*4,0xffffff,true);}
 }
 for(const auto &a:annotations){size_t k=0;while(k<a.length){
  auto found=byRecord.find(positions[a.start+k]);if(found==byRecord.end()){++k;continue;}const Glyph &first=visible[found->second];size_t stop=k+1;const Glyph* last=&first;
  while(stop<a.length){auto j=byRecord.find(positions[a.start+stop]);if(j==byRecord.end()||visible[j->second].y!=first.y)break;last=&visible[j->second];++stop;}
  size_t lo=k*a.reading.size()/a.length,hi=stop*a.reading.size()/a.length;
  bool dots=a.reading.find_first_not_of(L"\x00b7")==std::wstring::npos;
  if(dots&&a.reading.size()==a.length){for(size_t v=k;v<stop;++v){const auto &g=visible[byRecord[positions[a.start+v]]];Bitmap b=reading(L"\x00b7");int x=(g.x+g.left)*4+g.width*2-b.w/2,y=g.y*4-16-b.h;paint(b,x,y,0xffffff,true);ink.push_back({1,a.unit,a.span,(int)v,(int)v,1,x/4.f,y/4.f,b.w/4.f,b.h/4.f});}}
  else if(hi>lo){std::wstring part=a.reading.substr(lo,hi-lo);Bitmap b=reading(part);
   float left=(float)(first.x+first.left),right=(float)(last->x+last->left+last->width);
   int x=(int)((left+right)*2-b.w/2),y=first.y*4-4-b.h;
   x=std::max(48*4,std::min(914*4-b.w,x));paint(b,x,y,0xffffff,true);
   ink.push_back({1,a.unit,a.span,(int)k,(int)lo,(int)(hi-lo),x/4.f,y/4.f,b.w/4.f,b.h/4.f});}
  k=stop;
 }}
 Bitmap hint=reading(L"\ubb38\uc7a5\uc744 \uc120\ud0dd\ud558\uba74 \ud574\ub2f9 \uc2dc\uc810\uc73c\ub85c \ub3cc\uc544\uac11\ub2c8\ub2e4.");paint(hint,80*4,530*4,0xffffff,true);
 nativeRubySmall.assign(1024*576,0);for(int y=0;y<576;++y)for(int x=0;x<1024;++x){unsigned a=0;for(int yy=0;yy<4;++yy)for(int xx=0;xx<4;++xx)a+=nativeRuby[(y*4+yy)*BW+x*4+xx];nativeRubySmall[y*1024+x]=(unsigned char)((a+8)/16);}
 uploadPending=true;++generation;
}
static void nativeOverlay(){
 if(nativeRuby.empty())return;int w=0,h=0;uint32_t* bits=0;
 ((void(__cdecl*)(int*,int*,uint32_t**))*(void**)0x62961c)(&w,&h,&bits);
 if(bits&&w>=1024&&w<=16384&&h>=576){int* d=(int*)0x62949c;int l=std::max(0,d[0]),r=std::min(1024,d[2]+1),t=std::max(0,d[1]),bt=std::min(576,d[3]+1);
  for(int y=t;y<bt;++y)for(int x=l;x<r;++x){unsigned a=nativeRubySmall[y*1024+x];if(!a)continue;uint32_t &p=bits[y*w+x];unsigned b=p&255,g=(p>>8)&255,red=(p>>16)&255;p=((red+(255-red)*a/255)<<16)|((g+(255-g)*a/255)<<8)|(b+(255-b)*a/255);}
 }else ++errors;
 ((void(__cdecl*)())*(void**)0x629620)();
}
static void release(){if(texture){texture->Release();texture=0;}uploadPending=true;}
}
extern "C" __declspec(dllexport) void __cdecl N2HD_BacklogBegin(){Guard guard;PerfScope perf(PF_BACKLOG);Backlog::visible.clear();Backlog::readHistory();}
extern "C" __declspec(dllexport) int __cdecl N2HD_BacklogGlyph(void* font,int x,int y,const unsigned short* record){Guard guard;PerfScope perf(PF_BACKLOG);using namespace Backlog;if(!font||!record)return x;
 LOGFONTW lf={};GetObjectW(GetCurrentObject(*(HDC*)0x629864,OBJ_FONT),sizeof(lf),&lf);
 if(!fontKnown||memcmp(&lf,&Backlog::font,sizeof(lf))){Backlog::font=lf;fontKnown=true;glyphCache.clear();rubyCache.clear();advanceCache.clear();layoutHash=0;}
 int originalX=x;HDC dc=*(HDC*)0x629864;x=naturalX(dc,record,x);
 visible.push_back({record,*record,(unsigned)iv(font,12),x,y,iv(font,0x20),iv(font,0x5c),iv(font,0x60),iv(font,0x54),iv(font,0x58),originalX,advance(dc,*record)});return x;
}
extern "C" __declspec(dllexport) void __cdecl N2HD_BacklogEnd(){Guard guard;PerfScope perf(PF_BACKLOG);using namespace Backlog;if(visible.empty())return;
 unsigned jumpLo=0,jumpHi=0;N2HD_JumpHover(&jumpLo,&jumpHi);uint64_t h=hash(hash(historyHash,jumpLo),jumpHi);for(const auto &g:visible){h=hash(h,(uintptr_t)g.record);h=hash(h,g.code);h=hash(h,g.color);h=hash(h,g.x);h=hash(h,g.y);}
 if(h!=layoutHash){rebuild();layoutHash=h;}nativeOverlay();begin();if(!begun)return;
 if(!texture){lastError=dev->CreateTexture(BW,BH,1,D3DUSAGE_DYNAMIC,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&texture,0);uploadPending=true;if(FAILED(lastError))return;}
 if(uploadPending){D3DLOCKED_RECT l;lastError=texture->LockRect(0,&l,0,D3DLOCK_DISCARD);if(FAILED(lastError))return;for(int y=0;y<BH;++y)memcpy((char*)l.pBits+y*l.Pitch,pixels.data()+y*BW,BW*4);texture->UnlockRect(0);uploadPending=false;}
 int* d=(int*)0x62949c;RECT rc={(LONG)(std::max(0,d[0])*SCALE),(LONG)(std::max(0,d[1])*SCALE),(LONG)(std::min(1024,d[2]+1)*SCALE),(LONG)(std::min(576,d[3]+1)*SCALE)};
 if(rc.right<=rc.left||rc.bottom<=rc.top)return;V v[4]={{-.5f,-.5f,0,1,0xffffffff,0,0,0,0},{W-.5f,-.5f,0,1,0xffffffff,1,0,1,0},{W-.5f,H-.5f,0,1,0xffffffff,1,1,1,1},{-.5f,H-.5f,0,1,0xffffffff,0,1,0,1}};
 dev->SetPixelShader(pixelShader);float flags[4]={};dev->SetPixelShaderConstantF(0,flags,1);dev->SetTexture(0,texture);dev->SetTexture(1,0);dev->SetTexture(2,0);dev->SetTexture(3,0);dev->SetScissorRect(&rc);dev->SetRenderState(D3DRS_BLENDOP,D3DBLENDOP_ADD);dev->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);dev->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);lastError=dev->DrawPrimitiveUP(D3DPT_TRIANGLEFAN,2,v,sizeof(V));
}
extern "C" __declspec(dllexport) int __cdecl N2HD_BacklogLayout(Backlog::Ink* out,int capacity){Guard guard;PerfScope perf(PF_BACKLOG);int n=(int)Backlog::ink.size();if(out&&capacity>0)memcpy(out,Backlog::ink.data(),std::min(n,capacity)*sizeof(Backlog::Ink));return n;}
extern "C" __declspec(dllexport) void __cdecl N2HD_BacklogStats(uint64_t* out){Guard guard;out[0]=Backlog::generation;out[1]=Backlog::visible.size();out[2]=Backlog::annotations.size();out[3]=Backlog::errors;out[4]=Backlog::historyHash;out[5]=Backlog::layoutHash;}

// Read-only evidence: [record, code, original x, natural x, y, font advance].
extern "C" __declspec(dllexport) int __cdecl N2HD_BacklogPlacement(int* out,int capacity){Guard guard;PerfScope perf(PF_BACKLOG);using namespace Backlog;int n=(int)visible.size();if(out)for(int i=0;i<std::min(n,capacity);++i){const auto &g=visible[i];int* p=out+i*6;p[0]=(int)g.record;p[1]=g.code;p[2]=g.originalX;p[3]=g.x;p[4]=g.y;p[5]=g.advance;}return n;}
