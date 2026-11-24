"""Compare every lyric boundary against two forced alignments, independently decoded words and isolated vocal sustain."""
from pathlib import Path
from collections import Counter,defaultdict
from difflib import SequenceMatcher
import json,re,unicodedata
import numpy as np,soundfile as sf
from scipy import signal,ndimage
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s).casefold() if c.isalnum())
def asr_edge(words,text,t,tail):
    target=norm(text);target=target[-17:] if tail else target[:17]
    if len(target)<3:return None
    candidates=[]
    for i,w in enumerate(words):
        mark=w['end' if tail else 'start']
        if abs(mark-t)>2.3:continue
        ss=(words[max(0,i-6):i+1] if tail else words[i:i+7])
        text2=norm(''.join(k['word'] for k in ss));text2=text2[-len(target):] if tail else text2[:len(target)]
        sim=SequenceMatcher(None,target,text2,autojunk=False).ratio()
        if sim>=.7 and abs(w['end']-w['start'])<3:
            candidates.append((sim-.045*abs(mark-t),round(mark,2),round(sim,2)))
    if candidates:
        _,v,q=max(candidates);return [v,q]
def envelope(tr):
    y,fs=sf.read(HERE/'vocals'/(tr+'.flac'),dtype='float32')
    fil=signal.sosfilt(signal.butter(3,[135,6100],btype='bandpass',fs=fs,output='sos'),y)
    n=len(fil)//160
    db=10*np.log10(np.maximum(ndimage.uniform_filter1d(np.mean(fil[:n*160].reshape(-1,160)**2,axis=1),7),1.e-12))
    return db
def stable_runs(mask,minimum):
    ix=np.flatnonzero(np.diff(np.r_[False,mask,False].astype('int8'))).reshape(-1,2)
    return [(int(a),int(b)) for a,b in ix if b-a>=minimum]
def calc(tr,rs):
    al=json.loads((HERE/'align'/(tr+'.json')).read_text(encoding='utf8'))
    dec=[]
    for nm in ('large','turbo'):
        j=json.loads((ROOT/'data'/(tr+'.'+nm+'.json')).read_text(encoding='utf8'))
        dec.append([w for s in j['segments'] for w in (s.get('words') or [])])
    db=envelope(tr);out=[]
    for i,r in enumerate(rs):
        s,e=r['start']/1000,r['end']/1000;a,b=al['mix'][i],al['vocals'][i]
        threshold=float(np.clip(np.quantile(db[round((s+.12)*100):round(e*100)],.73)-17,-54,-33))
        out.append(dict(id=r['id'],track=tr,old=[s,e],new=[s,e],gate=round(threshold,1),
                        mix=[a['s'],a['e']],vocals=[b['s'],b['e']],confidence=[a['prob'],b['prob']],
                        head=[asr_edge(ws,r['source'],s,False) for ws in dec],tail=[asr_edge(ws,r['source'],e,True) for ws in dec],why=[]))
    for i,v in enumerate(out):
        s,e=v['old'];pred=out[i-1] if i else None
        a,b=al['mix'][i],al['vocals'][i]
        def update_start(start,reason):
            start=round(start,1)
            if start<=0 or start>=e-.6 or abs(start-s)<.19:return
            if pred and (start<pred['old'][0]+.7):return
            v['new'][0]=start;v['why'].append(reason)
            if pred and (abs(s-pred['old'][1])<=.3 or pred['new'][1]>start):
                pred['new'][1]=start;pred['why'].append('shared boundary')
        evidence=[x[0] for x in v['head'] if x and x[1]>=.72]
        if pred and s-pred['old'][1]<=.30:
            # Only adjoining phrases may share a DTW boundary. Clip endpoints and time spent in a rest are unreliable.
            fa=[x['s'] for x in (a,b) if not x['first']]
            if len(fa)==2 and max(fa)-min(fa)<=.32:
                c=float(np.median(fa))
                tail=[x[0] for x in pred['tail'] if x and x[1]>=.72]
                corroborated=[x for x in evidence+tail if abs(x-c)<=.38]
                if abs(c-s)<=1.55 and corroborated:
                    update_start(float(np.median(fa+corroborated))+.04,'shared sung phrase onset')
        else:
            # After a real rest, require a sustained onset in the stem and a matching independent lexical anchor.
            left=round(max(0,s-1.8)*100);right=round((s+1.9)*100)
            activity=db[left:right]>v['gate']+2
            active=stable_runs(activity,13)
            candidates=[]
            for l,h in active:
                at=(l+left)/100
                if l<17 or np.mean(activity[l-17:l])>.18:continue
                if evidence and min(abs(at-x) for x in evidence)<=.36:candidates.append(at)
            if candidates:
                onset=min(candidates,key=lambda x:abs(x-s))
                if .42<=abs(onset-s)<=1.45:update_start(onset-.07,'isolated vocal onset')
    for i,v in enumerate(out):
        s,e=v['old'];nxt=out[i+1]['new'][0] if i+1<len(out) else len(db)/100-.03
        if nxt-v['new'][1]<.30:continue
        start=round(e*100);limit=min(round((e+7.3)*100),round(nxt*100),len(db)-1)
        if limit<start+26:continue
        active=db>v['gate']
        if np.mean(active[max(0,start-24):start+14])<.58 or np.mean(active[start:start+19])<.60:continue
        low=stable_runs(~active[start:limit],23)
        if not low:
            if nxt-e<=1.3 and np.mean(active[start:limit])>.72:tail=nxt
            else:
                if nxt-e>1.3:v['review']='sustained with no isolated release'
                continue
        else:tail=(start+low[0][0])/100+.12
        if tail-e>.22:
            t=min(nxt,round(tail,1));v['new'][1]=t;v['why'].append('sustained vocal release')
    # A line may already have crossed its following onset in an older table.
    for i,v in enumerate(out):
        if i+1<len(out):v['new'][1]=min(v['new'][1],out[i+1]['new'][0])
        assert v['new'][1]-v['new'][0]>=.45,(tr,v)
    return out
if __name__=='__main__':
    old=HERE/'source-cues.json'
    if not old.exists():old.write_bytes((ROOT/'data/lyrics.json').read_bytes())
    cues=json.loads(old.read_text(encoding='utf8'))['cues'];allrows=[]
    for tr in dict.fromkeys(c['track'] for c in cues):
        rows=calc(tr,[c for c in cues if c['track']==tr]);allrows+=rows
        print(tr,len(rows),'changed',sum(v['old']!=v['new'] for v in rows),'large',[(v['id'],round(v['new'][1]-v['old'][1],1)) for v in rows if v['new'][1]-v['old'][1]>1.6],'check',[v['id'] for v in rows if v.get('review')],flush=True)
    (HERE/'audit.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
