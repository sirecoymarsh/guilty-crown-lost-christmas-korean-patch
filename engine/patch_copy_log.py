"""시험 기록: 글자 복사(copyGlyph)마다 원본·대상·위치·색·덮어쓰기 여부(N2HD_GLYPH_LOG 일 때 copy.log). 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:60], s.count(old))
    s = s.replace(old, new)


rep('static void copyGlyph(void* dst,void* src,int x,int y,uint32_t color,bool overwrite){\n',
    'static std::unordered_map<void*,unsigned> glyphCodes;   // test log only\n'
    'static void copyGlyph(void* dst,void* src,int x,int y,uint32_t color,bool overwrite){\n'
    ' {static int clog=-1;static FILE* cf;if(clog<0){wchar_t d[MAX_PATH];clog=GetEnvironmentVariableW(L"N2HD_GLYPH_LOG",0,0)&&GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",d,MAX_PATH)?1:0;if(clog)cf=_wfopen((std::wstring(d)+L"\\\\copy.log").c_str(),L"a");}\n'
    '  if(cf&&dst&&src){void* sk=pv(src,0x28);auto gc=glyphCodes.find(sk);auto hs=high.find(sk);fprintf(cf,"%c src=%p %dx%d code=%04x hi=%d dst=%p %dx%d at=%d,%d color=%06x dsthi=%d\\n",overwrite?\'M\':\'c\',sk,iv(src,8),iv(src,12),gc==glyphCodes.end()?0:gc->second,hs!=high.end()?hs->second.w:0,pv(dst,0x28),iv(dst,8),iv(dst,12),x,y,color&0xffffff,high.count(pv(dst,0x28))?1:0);fflush(cf);}}\n')
rep(' high[native]=std::move(h);++glyphs;\n}', ' glyphCodes[native]=code;high[native]=std::move(h);++glyphs;\n}')
p.write_text(s, 'utf-8'); print('ok')
