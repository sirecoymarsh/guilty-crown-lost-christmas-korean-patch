"""시험 기록: 4배 글자마다 1배 칸·4배 잉크 크기·잘린 잉크 비율(N2HD_PROFILE_DIR + N2HD_GLYPH_LOG 일 때만 glyph.log). 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')
old = ' high[native]=std::move(h);++glyphs;\n}'
assert s.count(old) == 1
new = r''' {static int glog=-1;static wchar_t gdir[MAX_PATH];if(glog<0)glog=GetEnvironmentVariableW(L"N2HD_GLYPH_LOG",0,0)&&GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",gdir,MAX_PATH)?1:0;
  if(glog){double all=0,lost=0;for(unsigned y=0;y<big.gmBlackBoxY;++y)for(unsigned x=0;x<big.gmBlackBoxX;++x){double a=buf[y*pitch+x];all+=a;int tx=dx+x,ty=dy+y;if(tx<0||tx>=h.w||ty<0||ty>=h.h)lost+=a;}
   FILE* f=_wfopen((std::wstring(gdir)+L"\\glyph.log").c_str(),L"a");if(f){fprintf(f,"%04x dim=%d %dx%d bb=%ux%u o=%ld,%ld big=%ux%u o=%ld,%ld d=%d,%d lost=%.1f flags=%08x\n",code,dim!=dimensions.end()?1:0,width,height,gm->gmBlackBoxX,gm->gmBlackBoxY,gm->gmptGlyphOrigin.x,gm->gmptGlyphOrigin.y,big.gmBlackBoxX,big.gmBlackBoxY,big.gmptGlyphOrigin.x,big.gmptGlyphOrigin.y,dx,dy,all?lost*100/all:0.0,iv(font,8));fclose(f);}}}
 high[native]=std::move(h);++glyphs;
}'''
s = s.replace(old, new)
p.write_text(s, 'utf-8'); print('ok')
