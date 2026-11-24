"""Apply the same ordered, size-preserving substitutions as the native reader to real saved programs."""
import collections, hashlib, json, re, struct
from pathlib import Path
from package import AW, BGM, HERE, INV, LIVE, NPA, compact, decode_program, new, old, patched, sha, update_lookup

def replace_payload(data, table):
    size, anchor_length, count = struct.unpack_from('<III',table,8)
    anchor = table[52:52+anchor_length]
    if not 0 < count <= 256 or data[:4] != b'NPSF':
        raise ValueError('Invalid table or save header')
    pos=16
    while True:
        at=data.find(anchor,pos)
        if at<0:return data
        pos=at+len(anchor)
        before=data[pos:pos+size]
        if sha(before)==table[20:52].hex():
            data=data[:pos]+patched(before,table,anchor)+data[pos+size:]
            pos+=size

def script(run):
    return next(run.glob('profile/Nitroplus/*/1.00/0011/script.npf')).read_bytes()

def verify_saved_views():
    oldtables=[(BGM/'payload/lyrics-resume'/n).read_bytes() for n in ['data.n2l','repair-v1.n2l','loop.n2l','repair-loop-v1.n2l']]
    extra=[(HERE/'tables'/n).read_bytes() for n in ['timing-legacy.n2l','timing-lf.n2l','timing-crlf.n2l']]
    def apply(data,ts):
        for t in ts:data=replace_payload(data,t)
        return data
    legacy=script(AW/'runs/regular-old-slot')
    broken=script(BGM/'runs/chapter-sword')
    corrected=apply(legacy,oldtables)
    modern=script(AW/'runs/exact-embedded')
    head=extra[2][52:52+struct.unpack_from('<I',extra[2],12)[0]]
    assert modern.find(head)>0
    text,key=decode_program(modern)
    enc=bytes(INV[(i+key)&255] for i in range(256))
    test_lf=b'\0test\0'+text[text.index(b'function KrLyLookup()\r\n{\r\n'):].replace(b'\r\n',b'\n')
    body=test_lf.translate(enc)
    modern_lf=b'NPSF'+struct.pack('<III',len(body),len(body),0)+body
    out={}
    for name,raw in [('original-slot',legacy),('old-patch-slot',broken),('previous-bgm-repair-view',corrected),('modern-crlf-slot',modern),('modern-lf-fixture',modern_lf)]:
        updated=apply(raw,oldtables+extra)
        assert updated!=raw and len(raw)==len(updated) and apply(updated,oldtables+extra)==updated,name
        if name.startswith('modern'):
            plain=updated[16:].translate(bytes(enc.index(i) for i in range(256)))
            pairs=[(int(k),int(a),int(b)) for a,b,k in re.findall(rb'\$(?:KLT|KLY_TIME)>=(\d+)&&\$(?:KLT|KLY_TIME)<(\d+)\)\{\$KLY_CUE=(\d+);\}',plain)]
            expected=[(r['id'],r['start'],r['end']) for r in new]
            assert pairs and len(pairs)%len(expected)==0 and pairs==expected*(len(pairs)//len(expected)),name
        else:
            plain,_=decode_program(updated)
            copies=plain.count(b'$AWfirst=0;\r\n ');assert copies>0
            for tr in dict.fromkeys(r['track'] for r in new):
                needle=b'$AWt="'+compact([r for r in new if r['track']==tr])+b'";'
                assert plain.count(needle)==copies,(name,tr)
        out[name]={'file_sha256':sha(raw),'view_sha256':sha(updated),'checked_cues':len(new),'same_length':True,'idempotent':True}
    return out

def verify_sources():
    import soundfile as sf
    from io import BytesIO
    references=NPA(LIVE/'sound.npa')
    audio={e['name']:e for e in references.entries if e['type']==2}
    metrics={}
    for tr in dict.fromkeys(r['track'] for r in new):
        local=(HERE.parent/'audio'/(tr+'.ogg')).read_bytes()
        assert local==references.read(audio['bgm\\'+tr+'.ogg']),tr
        info=sf.info(BytesIO(local));length=info.frames/info.samplerate
        a=[r for r in old if r['track']==tr];b=[r for r in new if r['track']==tr]
        assert all((x['id'],x['track'],x['source'],x['ko'])==(y['id'],y['track'],y['source'],y['ko']) for x,y in zip(a,b))
        assert all(0<=r['start']<r['end']<=length*1000 for r in b) and all(x['end']<=y['start'] for x,y in zip(b,b[1:]))
        changed=sum((x['start'],x['end'])!=(y['start'],y['end']) for x,y in zip(a,b))
        metrics[tr]={'cues':len(b),'changed':changed,'later_ends':sum(y['end']>x['end'] for x,y in zip(a,b)),'last_sung_end':b[-1]['end']/1000,'track_length':round(length,3),'ogg_sha256':sha(local)}
    return metrics

if __name__=='__main__':
    result={'sound_and_cues':verify_sources(),'save_views':verify_saved_views()}
    (HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('Verified game audio, 366 ordered cues and five independently resolved save representations')
