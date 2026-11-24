// Button hit test with Zoom (Claude 11-02). The engine's choice hover/click test (0x4525e0, loop at 0x452715) checks every
// picture in a button's MouseUsual state at its full texture size from its position, and the pixel's alpha there; it ignores
// Zoom. The Korean 4K build draws the title, CG gallery, Yes/No dialog, backlog exit and right-click menu labels from 4x
// pictures (768x144) zoomed to 25%, so each label also answered for an invisible 4x copy reaching far right and down: the
// pointer below the menu showed the hand, and a click on Load also hit Start's invisible copy, and Start won (user 11-02
// "whatever I click on the title starts a new game"). Here a zoomed picture is tested where it is drawn: the pointer is
// mapped through the drawn rectangle (the transform's screen and source corners, as N2HD_Draw draws it) back to a texel.
// Unzoomed pictures keep the engine's own test. N2HD_TEST_HIT_ORIGINAL=1 keeps the engine's test for all.
static int __cdecl hitTestZoom(void* o,int cx,int cy,void* node){
 static int orig=-1;if(orig<0)orig=GetEnvironmentVariableA("N2HD_TEST_HIT_ORIGINAL",0,0)?1:0;
 void* t=pv(o,0x2c);if(!t)return 0;int w=iv(t,8),h=iv(t,12);uint32_t** rows=(uint32_t**)pv(t,0x2c);if(!rows||w<1||h<1)return 0;
 int px=iv(o,0x10),py=iv(o,0x14),u,v;bool zoomed=false;
 void* m=pv(o,0x28);
 if(m&&!orig){short* sx=(short*)((char*)m+0x70),*sy=(short*)((char*)m+0x78),*x=(short*)((char*)m+0x80),*y=(short*)((char*)m+0x88);
  bool rectangle=x[0]==x[3]&&x[1]==x[2]&&y[0]==y[1]&&y[2]==y[3];
  int x0=std::min(x[0],x[1]),x1=std::max(x[0],x[1]),y0=std::min(y[0],y[2]),y1=std::max(y[0],y[2]);
  int s0=*std::min_element(sx,sx+4),s1=*std::max_element(sx,sx+4),t0=*std::min_element(sy,sy+4),t1=*std::max_element(sy,sy+4);
  if(rectangle&&x1>x0&&y1>y0&&s1>s0&&t1>t0&&(x1-x0!=s1-s0||y1-y0!=t1-t0)){
   if(cx<x0||cx>x1||cy<y0||cy>y1)return 0;
   u=s0+(int)((long long)(cx-x0)*(s1-s0)/(x1-x0));v=t0+(int)((long long)(cy-y0)*(t1-t0)/(y1-y0));zoomed=true;}}
 if(!zoomed){if(cy<py||cy>=py+h||cx<px||cx>=px+w)return 0;u=cx-px;v=cy-py;}
 if(u<0||v<0||u>=w||v>=h)return 0;
 void* clip=node?pv(node,0x1374):0;   // the button's own clip rectangle, tested as the engine does
 if(clip&&(cx<iv(clip,0x34)||cx>iv(clip,0x3c)+iv(clip,0x34)||cy<iv(clip,0x38)||cy>iv(clip,0x40)+iv(clip,0x38)))return 0;
 return rows[v]&&((rows[v][u]>>24)!=0);}
extern "C" int __cdecl N2HD_HitTest(void* o,int cx,int cy,void* node){return hitTestZoom(o,cx,cy,node);}   // reads engine objects only: no renderer lock
