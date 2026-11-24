"""hires_art.inc: 타일로 나눈 4배 그림(<key>_0.jxl ...)을 읽게 고침. 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\hires_art.inc'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


rep("struct JxlRowOut {ArtBands* bands;int pitch;int ch;};\nstatic void artRow(void* opaque,size_t x,size_t y,size_t n,const void* pixels){auto o=(JxlRowOut*)opaque;uint8_t* d=(*o->bands)[y/ART_BAND].data()+(y%ART_BAND)*o->pitch+x*4;",
    "struct JxlRowOut {ArtBands* bands;int pitch;int ch;int y0;};\nstatic void artRow(void* opaque,size_t x,size_t y,size_t n,const void* pixels){auto o=(JxlRowOut*)opaque;y+=o->y0;uint8_t* d=(*o->bands)[y/ART_BAND].data()+(y%ART_BAND)*o->pitch+x*4;")
rep("static bool artDecode(const std::vector<uint8_t>& buf,const ArtEntry& e,ArtBands& bands,int pitch,ArtMem& mem){",
    "// One file (the whole art, or one tile): its rows land at y0.. in the bands.\nstatic bool artDecode(const std::vector<uint8_t>& buf,const ArtEntry& e,int y0,int rows,ArtBands& bands,int pitch,ArtMem& mem){")
rep("JxlRowOut out{&bands,pitch,e.alpha?4:3};", "JxlRowOut out{&bands,pitch,e.alpha?4:3,y0};")
rep("(int)bi.xsize!=e.ow||(int)bi.ysize!=e.oh)break;}", "(int)bi.xsize!=e.ow||(int)bi.ysize!=rows)break;}")
rep(""" {HANDLE h=CreateFileW(e.path.c_str(),GENERIC_READ,FILE_SHARE_READ,0,OPEN_EXISTING,FILE_FLAG_SEQUENTIAL_SCAN,0);std::vector<uint8_t> buf;
  if(h==INVALID_HANDLE_VALUE)why="open";
  else{DWORD size=GetFileSize(h,0),got=0;try{buf.resize(size);}catch(...){why="file buffer";}if(!why&&(!size||!ReadFile(h,buf.data(),size,&got,0)||got!=size))why="read";CloseHandle(h);}
  if(!why)try{bands.resize((th+ART_BAND-1)/ART_BAND);for(size_t i=0;i<bands.size();++i)bands[i].resize((size_t)std::min(ART_BAND,th-(int)i*ART_BAND)*pitch);}catch(...){why="bands";}
  if(!why&&!artDecode(buf,e,bands,pitch,mem))why="decode";}
""", """ try{bands.resize((th+ART_BAND-1)/ART_BAND);for(size_t i=0;i<bands.size();++i)bands[i].resize((size_t)std::min(ART_BAND,th-(int)i*ART_BAND)*pitch);}catch(...){why="bands";}
 const int step=e.tile>0?e.tile:e.oh;
 for(int y0=0,i=0;!why&&y0<e.oh;y0+=step,++i){std::wstring file=e.tile>0?e.path+L"_"+std::to_wstring(i)+L".jxl":e.path+L".jxl";std::vector<uint8_t> buf;
  HANDLE h=CreateFileW(file.c_str(),GENERIC_READ,FILE_SHARE_READ,0,OPEN_EXISTING,FILE_FLAG_SEQUENTIAL_SCAN,0);
  if(h==INVALID_HANDLE_VALUE){why="open";break;}
  DWORD size=GetFileSize(h,0),got=0;try{buf.resize(size);}catch(...){why="file buffer";}if(!why&&(!size||!ReadFile(h,buf.data(),size,&got,0)||got!=size))why="read";CloseHandle(h);
  if(!why&&!artDecode(buf,e,y0,std::min(step,e.oh-y0),bands,pitch,mem))why="decode";}
""")
rep('fprintf(artLog,"upload %ls %dx%d %llums ok jxl_max_alloc %uKB\\n",e.path.c_str(),tw,th,(unsigned long long)ms,(unsigned)(mem.largest>>10));',
    'fprintf(artLog,"upload %ls.jxl %dx%d %llums ok jxl_max_alloc %uKB tile %d\\n",e.path.c_str(),tw,th,(unsigned long long)ms,(unsigned)(mem.largest>>10),e.tile);')
rep('fprintf(artLog,"upload %ls %dx%d %llums FAIL %s jxl_max_alloc', 'fprintf(artLog,"upload %ls.jxl %dx%d %llums FAIL %s jxl_max_alloc')
rep('fprintf(artLog,"stale %ls engine', 'fprintf(artLog,"stale %ls.jxl engine')
p.write_text(s, 'utf-8')
print('ok')
