"""hires_art.inc: 4배 그림 올리기를 프레임마다 4ms 안쪽으로 나눠 함(큰 그림 한 장에 0.08~0.09초 멈추던 것). 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\hires_art.inc'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, (old[:80], s.count(old))
    s = s.replace(old, new)


rep('volatile LONG state=0;LONG64 counted=0;', 'volatile LONG state=0;LONG64 counted=0;bool wanted=false;')
start = s.index('// Finished bands -> POOL_DEFAULT texture in the cache.')
end = s.index('// Frame pacing for the test log')
s = s[:start] + r'''// Finished bands -> POOL_DEFAULT texture, a few bands per frame end (ART_UPLOAD_MS): one 60 MB picture in one go held
// the frame 80-90 ms (10-27). One upload at a time; the picture is drawn from its 1x pixels until it is in the cache.
static const double ART_UPLOAD_MS=4.0;
struct ArtUp {std::shared_ptr<ArtJob> job;IDirect3DTexture9* tx=0;IDirect3DSurface9* dst=0;IDirect3DSurface9* strip=0;int y=0;double ms=0;};
static std::unique_ptr<ArtUp> artUp;
static void artUpEnd(const char* why){ArtUp& u=*artUp;ArtJob& j=*u.job;if(u.strip)u.strip->Release();if(u.dst)u.dst->Release();
 if(why&&u.tx){u.tx->Release();u.tx=0;}
 ArtBands().swap(j.bands);if(j.counted){InterlockedAdd64(&artPendingBytes,-j.counted);j.counted=0;}
 if(u.ms>artUploadMsMax)artUploadMsMax=(uint64_t)u.ms;
 if(u.tx){artCacheRemove(j.e);size_t bytes=(size_t)j.tw*j.th*4;artCache[j.e]={u.tx,j.tw,j.th,frames,bytes};artCacheBytes+=bytes;++artUploads;artEvict();}else{++artFails;artBad.insert(j.e);}
 if(artLog){fprintf(artLog,"upload %ls.jxl %dx%d %.0fms %s decode %llums cache %uMB\n",j.e->path.c_str(),j.tw,j.th,u.ms,u.tx?"ok":why,(unsigned long long)j.decodeMs,(unsigned)(artCacheBytes>>20));fflush(artLog);}
 artUp.reset();}
static void artUpStep(){LARGE_INTEGER f,a,b;QueryPerformanceFrequency(&f);QueryPerformanceCounter(&a);ArtUp& u=*artUp;ArtJob& j=*u.job;const int pitch=j.tw*4;
 if(!u.tx){if(FAILED(dev->CreateTexture(j.tw,j.th,1,0,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&u.tx,0))){u.tx=0;artUpEnd("texture");return;}
  if(FAILED(u.tx->GetSurfaceLevel(0,&u.dst))||FAILED(dev->CreateOffscreenPlainSurface(j.tw,ART_BAND,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&u.strip,0))){artUpEnd("strip");return;}}
 for(;;){int n=std::min(ART_BAND,j.th-u.y);D3DLOCKED_RECT l;if(FAILED(u.strip->LockRect(&l,0,0))){artUpEnd("lock");return;}
  const uint8_t* band=j.bands[u.y/ART_BAND].data();for(int y=0;y<n;++y)memcpy((uint8_t*)l.pBits+(size_t)y*l.Pitch,band+(size_t)y*pitch,pitch);u.strip->UnlockRect();
  RECT r{0,0,j.tw,n};POINT p{0,u.y};if(FAILED(dev->UpdateSurface(u.strip,&r,u.dst,&p))){artUpEnd("update");return;}
  std::vector<uint8_t>().swap(j.bands[u.y/ART_BAND]);u.y+=n;
  QueryPerformanceCounter(&b);double ms=(b.QuadPart-a.QuadPart)*1000.0/f.QuadPart;
  if(u.y>=j.th){u.ms+=ms;artUpEnd(0);return;}
  if(ms>=ART_UPLOAD_MS){u.ms+=ms;return;}}}
// Each frame end: go on with the upload in progress, or start the next finished job (pictures being drawn first).
static void artFrameEnd(){if(!dev)return;if(!artUp&&artJobs.empty())return;if(dev->TestCooperativeLevel()!=D3D_OK)return;
 if(!artUp){auto pick=artJobs.end();
  for(auto it=artJobs.begin();it!=artJobs.end();){LONG s=it->second->state;
   if(s==3){artBad.insert(it->first);++artFails;it=artJobs.erase(it);continue;}
   if(s==2&&(pick==artJobs.end()||(it->second->wanted&&!pick->second->wanted)))pick=it;++it;}
  if(pick==artJobs.end())return;
  artUp.reset(new ArtUp);artUp->job=pick->second;artJobs.erase(pick);}
 artUpStep();}
static void artRelease(){for(auto &c:artCache)c.second.tex->Release();artCache.clear();artCacheBytes=0;
 if(artUp){if(artUp->strip)artUp->strip->Release();if(artUp->dst)artUp->dst->Release();if(artUp->tx)artUp->tx->Release();artUp.reset();}}
''' + s[end:]
rep(''' auto it=artJobs.find(e);
 if(it!=artJobs.end()&&it->second->tw==tw&&it->second->th==th){''',
    ''' if(artUp&&artUp->job->e==e&&artUp->job->tw==tw&&artUp->job->th==th)return;
 auto it=artJobs.find(e);
 if(it!=artJobs.end()&&it->second->tw==tw&&it->second->th==th){if(urgent)it->second->wanted=true;''')
rep('auto j=std::make_shared<ArtJob>();j->e=e;j->tw=tw;j->th=th;artJobs[e]=j;',
    'auto j=std::make_shared<ArtJob>();j->e=e;j->tw=tw;j->th=th;j->wanted=urgent;artJobs[e]=j;')
rep(''' auto j=artJobs.find(e);
 if(j!=artJobs.end()&&j->second->tw==tw&&j->second->th==th&&(j->second->state==2||j->second->state==3)){IDirect3DTexture9* tx=artFinish(j);if(tx){artCache[e].lastFrame=frames;boundUV=0;}return tx;}
 artRequest(e,tw,th,true);++artLate;return 0;}''',
    ''' artRequest(e,tw,th,true);++artLate;return 0;}''')
p.write_text(s, 'utf-8')
print('ok')
