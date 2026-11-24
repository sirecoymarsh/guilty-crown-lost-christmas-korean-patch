"""Update only the lookup timing bytes, preserving all artwork and other scripts from each exact build."""
import hashlib,json,re,shutil,struct,sys
from pathlib import Path
HERE=Path(r'P:\AI\Codex\projects\gclx-song-20261123\timing-20261124');ROOT=HERE.parent;AW=ROOT/'awakening';BGM=AW/'bgm-output'
sys.path[:0]=[str(BGM),str(AW),str(ROOT/'tools')]
from make_tables import patched,transitions
from clock_patch import modern,legacy
from npa_adapter import NPA,INV
from save_lyrics import MODULE,decode_program
LIVE=Path(r'P:\AI\gclx-codexrun\game');SHARED=Path(r'F:\AI\gclx-4k\release_1121')
sha=lambda b:hashlib.sha256(b).hexdigest()
old=json.loads((HERE/'source-cues.json').read_text(encoding='utf8'))['cues'];new=json.loads((HERE/'accepted.json').read_text(encoding='utf8'))['cues']
row=re.compile(rb'^ *(if\(\$KLY_TRACK==\d+&&\$KLY_TIME>=)(\d+)(&&\$KLY_TIME<)(\d+)(\)\{\$KLY_CUE=(\d+);\}) *$',re.M)
def update_lookup(src):
    got=[]
    def sub(m):
        i=int(m[6])-1;a,b=old[i],new[i];assert a['id']==b['id']==i+1 and (int(m[2]),int(m[4]))==(a['start'],a['end'])
        got.append(i)
        if a['start']==b['start'] and a['end']==b['end']:return m[0]
        body=m[1]+str(b['start']).encode()+m[3]+str(b['end']).encode()+m[5]
        if len(body)>len(m[0]):raise ValueError(('No room in NSS row',i+1))
        return b' '*(len(m[0])-len(body))+body
    res=row.sub(sub,src);assert got==list(range(len(new))) and len(res)==len(src)
    return modern(res)
def archive(source,folder):
    folder.mkdir(parents=True,exist_ok=True)
    a=NPA(source);e=next(x for x in a.entries if x['name']=='kr_lyrics.nss');before=a.read(e)
    known=HERE/'archive-check.json'
    already=known.is_file() and sha(before)==json.loads(known.read_text(encoding='utf8'))['new_table_source']
    after=before if already else update_lookup(before)
    target=folder/'nss.npa'
    target.write_bytes(a.blob if already else a.pack({'kr_lyrics.nss':after}));out=NPA(target)
    assert [x['name'] for x in a.entries]==[x['name'] for x in out.entries]
    for x,y in zip(a.entries,out.entries):
        if x['name']=='kr_lyrics.nss':assert out.read(y)==after
        elif x['type']==2:assert a.raw(x)==out.raw(y)
    return {'source':str(source),'source_hash':sha(a.blob),'target_hash':sha(out.blob),'unchanged_entries':len([x for x in a.entries if x['type']==2])-1},before,after
def compact(rows):
    a='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
    def pair(n):
        v=n//100;assert n%100==0 and v<4096
        return a[v//64]+a[v%64]
    return ''.join(pair(r['start'])+pair(r['end']) for r in rows).encode()
def payload():
    main,before,after=archive(LIVE/'nss.npa',HERE/'play')
    latest,_,_=archive(SHARED/'staging/nss_play.npa',HERE/'latest')
    raw,k=decode_program((AW/'runs/regular-old-slot/profile/Nitroplus/GUILTY CROWN LOST XMAS/1.00/0011/script.npf').read_bytes())
    enc=bytes(INV[(i+k)&255] for i in range(256))
    tables=HERE/'tables';tables.mkdir(exist_ok=True)
    def extra(name,anchor,a,b):
        anchor=anchor.translate(enc);a=a.translate(enc);b=b.translate(enc)
        data=transitions(a,b,anchor);assert patched(a,data,anchor)==b
        print(name,len(data),'spans',struct.unpack_from('<I',data,16)[0])
        (tables/name).write_bytes(data)
    head=b'function KrLyLookup()\n{\n';i=before.index(head)
    assert before[:i]==after[:i]
    for nl,name in [(b'\n','timing-lf.n2l'),(b'\r\n','timing-crlf.n2l')]:
        extra(name,head.replace(b'\n',nl),before[i+len(head):].replace(b'\n',nl),after[i+len(head):].replace(b'\n',nl))
    m=MODULE.search(raw);common=raw[m.end():m.end()+struct.unpack('<I',m[1])[0]]
    anchor=raw[m.start():m.end()].translate(enc);p2=patched(common.translate(enc),(BGM/'payload/lyrics-resume/data.n2l').read_bytes(),anchor)
    dec=bytes(enc.index(j) for j in range(256));common=p2.translate(dec)
    head=b'$AWt="";$AWfirst=0;\r\n ';start=common.index(head)+len(head);end=common.index(b'  $AWy=14;',start)
    data=common[start:end];newdata=data
    for tr in dict.fromkeys(c['track'] for c in old):
        original=compact([c for c in old if c['track']==tr]);updated=compact([c for c in new if c['track']==tr])
        assert newdata.count(original)==1 and len(original)==len(updated)
        newdata=newdata.replace(original,updated)
    extra('timing-legacy.n2l',head,data,legacy(newdata))
    report={'play':main,'latest':latest,'old_table_source':sha(before),'new_table_source':sha(after),'stable_ids':len(new)}
    (HERE/'archive-check.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(main,latest)
if __name__=='__main__':payload()
