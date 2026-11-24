"""시험 기록 4: 그리기 변환의 +0xf0(화면 줄마다 [xmin,xmax] 20바이트 기록)이 있으면, 물체 범위 줄들의 구간을 같은 값끼리 묶어
draw3.log 에 덧붙인다. 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')
old = 'mm?pv(mm,0xf0):0,iv(object,0xc)&0xfff);fflush(df);}}\n'
assert s.count(old) == 1
new = r'''mm?pv(mm,0xf0):0,iv(object,0xc)&0xfff);
   if(mm&&pv(mm,0xf0)){short* ys=(short*)((char*)mm+0x88);int y0=std::max(0,(int)*std::min_element(ys,ys+4)),y1=std::min(575,(int)*std::max_element(ys,ys+4));short* sp=(short*)pv(mm,0xf0);int run=y0;
    for(int yy=y0;yy<=y1+1;++yy){if(yy<=y1&&yy>y0&&sp[yy*10]==sp[(yy-1)*10]&&sp[yy*10+1]==sp[(yy-1)*10+1]&&*(int*)((char*)mm+0x2df4+yy*4)==*(int*)((char*)mm+0x2df4+(yy-1)*4))continue;
     if(yy>y0)fprintf(df,"   rows %d-%d span %d..%d on=%d\n",run,yy-1,sp[run*10],sp[run*10+1],*(int*)((char*)mm+0x2df4+run*4));run=yy;}}
   fflush(df);}}
'''
s = s.replace(old, new)
p.write_text(s, 'utf-8'); print('ok')
