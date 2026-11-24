"""시험: N2HD_TEST_DUMP_CODE=<cp949 16진> 이면 그 글자를 복사할 때마다 원본 4배 글자와 복사 뒤 대상 층의 그 자리를
N2HD_PROFILE_DIR 에 raw(ARGB, 앞 8바이트 w,h)로 남긴다. 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')
old = '(p&0xff000000)|(color&0xffffff);}d.version=++serial;++copies;\n'
assert s.count(old) == 1
new = r'''(p&0xff000000)|(color&0xffffff);}d.version=++serial;++copies;
 {static unsigned dumpCode=~0u;static int dumps;static wchar_t dd[MAX_PATH];if(dumpCode==~0u){char v[16]={};dumpCode=GetEnvironmentVariableA("N2HD_TEST_DUMP_CODE",v,16)&&GetEnvironmentVariableW(L"N2HD_PROFILE_DIR",dd,MAX_PATH)?strtoul(v,0,16):0;}
  auto gc=glyphCodes.find(pv(src,0x28));if(dumpCode&&gc!=glyphCodes.end()&&gc->second==dumpCode&&dumps<8){++dumps;
   auto save=[&](const wchar_t* tag,const Hi& h,int x0,int y0,int w,int hh){wchar_t n[64];swprintf_s(n,L"\\dump%d_%s_%06x.raw",dumps,tag,color&0xffffff);FILE* f=_wfopen((std::wstring(dd)+n).c_str(),L"wb");if(!f)return;fwrite(&w,4,1,f);fwrite(&hh,4,1,f);
    for(int yy=0;yy<hh;++yy)for(int xx=0;xx<w;++xx){int sx=x0+xx,sy=y0+yy;uint32_t q=(sx>=0&&sx<h.w&&sy>=0&&sy<h.h)?h.data[sy*h.w+sx]:0;fwrite(&q,4,1,f);}fclose(f);};
   save(L"glyph",s,0,0,s.w,s.h);save(L"layer",d,ox-16,oy-16,s.w+32,s.h+32);}}
'''
s = s.replace(old, new)
p.write_text(s, 'utf-8'); print('ok')
