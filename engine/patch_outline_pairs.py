"""테두리(AROUND) 글자를 4배에서 꽉 차게: 엔진은 글자마다 같은 자리에 두 번 복사한다(본문 층, 더 어두운 색의 테두리 층).
테두리 층은 사방 2픽셀 8벌로 그리는데, 4배 획(5~6px)과 8px 간격 사이에 틈이 나 테두리가 따로 떨어진 그림자 여러 벌로 보였다
(사용자 10-27 「겹쳐보여」, 줄 구간 고침으로 본문이 4K 가 된 뒤 드러남). 짝 중 어두운 쪽 복사만 4배 2px 넓혀(원판 반지름 2)
8벌이 1배 때처럼 이어지게 한다. 시험 스위치 N2HD_TEST_OUTLINE_THIN=1: 넓히지 않음. 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')
old_start = 'static void copyGlyph(void* dst,void* src,int x,int y,uint32_t color,bool overwrite){\n'
old_tail = (' source=high.find(pv(src,0x28));Hi &s=source->second,&d=high.find(key)->second;int ox=x*4,oy=y*4;'
            'for(int yy=std::max(0,-oy);yy<s.h&&oy+yy<d.h;++yy)for(int xx=std::max(0,-ox);xx<s.w&&ox+xx<d.w;++xx)'
            '{uint32_t p=s.data[yy*s.w+xx];if(overwrite||(p>>24))d.data[(oy+yy)*d.w+ox+xx]=(p&0xff000000)|(color&0xffffff);}'
            'd.version=++serial;++copies;\n}\n')
assert s.count(old_start) == 1 and s.count(old_tail) == 1
s = s.replace(old_start, r'''static void copyInto(Hi& d,const uint32_t* sd,int sw,int sh,int ox,int oy,uint32_t color,bool overwrite){
 for(int yy=std::max(0,-oy);yy<sh&&oy+yy<d.h;++yy)for(int xx=std::max(0,-ox);xx<sw&&ox+xx<d.w;++xx){uint32_t p=sd[yy*sw+xx];if(overwrite||(p>>24))d.data[(oy+yy)*d.w+ox+xx]=(p&0xff000000)|(color&0xffffff);}}
// Outline (AROUND) text: the engine copies each glyph twice to the same spot, into the text layer and, in a darker colour,
// into an outline layer that it draws at 8 offsets of 2 px. At 4x those offsets leave gaps beside the 5-6 px strokes and the
// outline showed as separate ghost copies (user 10-27). The darker copy of such a pair is widened by 2 px (4x, a disc), which
// closes the 8 copies up as at 1x. N2HD_TEST_OUTLINE_THIN=1 leaves it thin.
static void widen(const Hi& s,std::vector<uint32_t>& out){out.assign(s.data.size(),0);
 for(int y=0;y<s.h;++y)for(int x=0;x<s.w;++x){uint32_t m=0;for(int dy=-2;dy<=2;++dy)for(int dx=-2;dx<=2;++dx){if(dx*dx+dy*dy>4)continue;int sx=x+dx,sy=y+dy;if(sx<0||sy<0||sx>=s.w||sy>=s.h)continue;uint32_t a=s.data[sy*s.w+sx]>>24;if(a>m)m=a;}out[y*s.w+x]=m<<24;}}
''' + old_start)
s = s.replace(old_tail, r''' source=high.find(pv(src,0x28));Hi &s=source->second,&d=high.find(key)->second;int ox=x*4,oy=y*4;
 static struct{void* src;void* dst;int x,y;uint32_t color;bool overwrite;} last={};static int thin=-1;if(thin<0)thin=GetEnvironmentVariableA("N2HD_TEST_OUTLINE_THIN",0,0)?1:0;
 void* skey=pv(src,0x28);bool pair=!thin&&skey==last.src&&x==last.x&&y==last.y&&key!=last.dst&&((color^last.color)&0xffffff)&&s.w*s.h<=512*512;
 auto luma=[](uint32_t c){return ((c>>16)&255)*3+((c>>8)&255)*6+(c&255);};static std::vector<uint32_t> wide;
 if(pair&&luma(color)<luma(last.color)){widen(s,wide);copyInto(d,wide.data(),s.w,s.h,ox,oy,color,overwrite);}
 else{copyInto(d,s.data.data(),s.w,s.h,ox,oy,color,overwrite);
  if(pair){auto pd=high.find(last.dst);if(pd!=high.end()){widen(s,wide);copyInto(pd->second,wide.data(),s.w,s.h,last.x*4,last.y*4,last.color,last.overwrite);pd->second.version=++serial;}}}
 last={skey,key,x,y,color,overwrite};
 d.version=++serial;++copies;
}
''')
p.write_text(s, 'utf-8'); print('ok')
