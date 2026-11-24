p = r'F:\AI\gclx-4k\engine\src\hires_art.inc'
s = open(p, encoding='utf-8').read()
rep = [
    ('struct ArtRef {const ArtEntry* e;uint32_t sig;};',
     'struct ArtRef {const ArtEntry* e;uint32_t sig;int pw,ph;};   // pw,ph: the engine surface size (width padded, 619 -> 620)'),
    (' if(artLog&&artLoads<=400){fprintf(artLog,"load %s -> %s %dx%d%s\\n",name,artNorm(name).c_str(),iv(t,8),iv(t,12),it==artIndex.end()?" (not in index)":(iv(t,8)!=it->second.w||iv(t,12)!=it->second.h)?" (size differs)":" MATCH");fflush(artLog);}\n if(it==artIndex.end()||iv(t,8)!=it->second.w||iv(t,12)!=it->second.h){art.erase(data);return;}\n art[data]={&it->second,artSig(t)};++artMatched;}',
     ' int pw=iv(t,8),ph=iv(t,12);bool fits=it!=artIndex.end()&&pw>=it->second.w&&pw<=it->second.w+7&&ph>=it->second.h&&ph<=it->second.h+7;\n if(artLog&&artLoads<=400){fprintf(artLog,"load %s %dx%d%s\\n",name,pw,ph,it==artIndex.end()?" (not in index)":fits?" MATCH":" (size differs)");fflush(artLog);}\n if(!fits){art.erase(data);return;}\n art[data]={&it->second,artSig(t),pw,ph};++artMatched;}'),
    ('static IDirect3DTexture9* artLoadTexture(const ArtEntry& e){',
     "// The texture covers the engine surface (pw x ph, padded) at the art's scale: the art in the top left, the padding\n"
     "// filled from its last column and row so bilinear sampling at the edge never reaches empty texels.\n"
     'static IDirect3DTexture9* artLoadTexture(const ArtEntry& e,int pw,int ph,int& tw,int& th){tw=(int)((double)pw*e.ow/e.w+0.5);th=(int)((double)ph*e.oh/e.h+0.5);if(tw<e.ow)tw=e.ow;if(th<e.oh)th=e.oh;'),
    ('if(FAILED(dev->CreateTexture(e.ow,e.oh,1,0,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&stage,0)))return 0;',
     'if(FAILED(dev->CreateTexture(tw,th,1,0,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&stage,0)))return 0;'),
    ('{ok=artDecode(buf,e,(uint8_t*)l.pBits,l.Pitch);stage->UnlockRect(0);}',
     '{uint8_t* base=(uint8_t*)l.pBits;ok=artDecode(buf,e,base,l.Pitch);\n'
     '  if(ok){for(int y=0;y<e.oh;++y){uint32_t* r=(uint32_t*)(base+(size_t)y*l.Pitch);for(int x=e.ow;x<tw;++x)r[x]=r[e.ow-1];}\n'
     '   for(int y=e.oh;y<th;++y)memcpy(base+(size_t)y*l.Pitch,base+(size_t)(e.oh-1)*l.Pitch,(size_t)tw*4);}\n'
     '  stage->UnlockRect(0);}'),
    ('if(ok&&SUCCEEDED(dev->CreateTexture(e.ow,e.oh,1,0,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&tx,0))',
     'if(ok&&SUCCEEDED(dev->CreateTexture(tw,th,1,0,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&tx,0))'),
    ('"upload %ls %dx%d %llums %s\\n",e.path.c_str(),e.ow,e.oh,', '"upload %ls %dx%d %llums %s\\n",e.path.c_str(),tw,th,'),
    (' if(iv(t,8)!=ar->second.e->w||iv(t,12)!=ar->second.e->h||artSig(t)!=ar->second.sig)',
     ' if(iv(t,8)!=ar->second.pw||iv(t,12)!=ar->second.ph||artSig(t)!=ar->second.sig)'),
    (' const ArtEntry* e=ar->second.e;IDirect3DTexture9* tx=artLoadTexture(*e);if(!tx){art.erase(ar);++artFails;return 0;}',
     ' const ArtEntry* e=ar->second.e;int tw=0,th=0;IDirect3DTexture9* tx=artLoadTexture(*e,ar->second.pw,ar->second.ph,tw,th);if(!tx){art.erase(ar);++artFails;return 0;}'),
    (' textures.push_back({t,data,e->ow,e->oh,ART_FMT,frames,1,tx,0});', ' textures.push_back({t,data,tw,th,ART_FMT,frames,1,tx,0});'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b, 1)
open(p, 'w', encoding='utf-8').write(s)
print('ok')
