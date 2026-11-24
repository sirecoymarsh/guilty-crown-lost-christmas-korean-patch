"""그리기 변환 +0xf0(화면 줄마다 [왼쪽,오른쪽) 자르기 구간)이 있는 물체를 1배 호환 길로 보내지 않고 4K 로 그린다.
본문 흰 글자 층이 늘 이 표를 달고 와서(10-27 시험: 구간은 줄 전체) 4K 화면의 본문 글자가 1배 확대본이었고, 맑은 고딕 1배
「덮」의 ㅓ 세로획이 GDI 글자 칸 밖으로 잘린 것까지 그대로 보였다(사용자 10-27). 엔진 래스터라이저(0x418860)는 이 표를
줄 자르기에만 쓴다(줄 매핑은 표와 상관없이 같음). 같은 구간인 줄끼리 잘라내기 사각형 하나로 묶어 그린다.
시험 스위치 N2HD_TEST_SPAN_COMPAT=1: 옛 동작(호환 길). 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:70], s.count(old))
    s = s.replace(old, new)


rep('static bool needsCompatibility(void* o,void* arg,void* filter){if(arg)return true;void* m=pv(o,0x28);if(m&&pv(m,0xf0))return true;',
    '// Row clip spans (+0xf0) are drawn on the GPU (N2HD_Draw); N2HD_TEST_SPAN_COMPAT=1 sends them down the 1x path as before.\n'
    'static bool spanCompat(){static int v=-1;if(v<0)v=GetEnvironmentVariableA("N2HD_TEST_SPAN_COMPAT",0,0)?1:0;return v!=0;}\n'
    'static bool needsCompatibility(void* o,void* arg,void* filter){if(arg)return true;void* m=pv(o,0x28);if(m&&pv(m,0xf0)&&spanCompat())return true;')
rep(' dev->SetScissorRect(&rc);dev->SetTexture(0,tex);lastError=dev->DrawPrimitiveUP(D3DPT_TRIANGLEFAN,2,v,sizeof(V));if(SUCCEEDED(lastError))++draws;\n}\n',
    r''' dev->SetTexture(0,tex);short* spans=(short*)pv(m,0xf0);
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
''')
p.write_text(s, 'utf-8'); print('ok')
