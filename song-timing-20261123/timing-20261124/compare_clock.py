"""Compare rendered final cues, game audio cursor and the reference waveform on the same time axis."""
import json,re
from collections import defaultdict
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy import ndimage,signal
HERE=Path(__file__).resolve().parent

def smooth(a):return ndimage.gaussian_filter1d(np.log(np.maximum(a,.001)),2.4)
def fit(ref,clock,peak,start,stop,estimate):
    grid=np.arange(start,stop,10)
    actual=smooth(np.interp(grid,clock,peak))
    actual-=np.mean(actual);width=len(actual)
    if width<140 or np.sum(actual**2)<.3:return None
    lo=max(0,round(estimate*100)-210);hi=min(len(ref),round(estimate*100)+210+width)
    search=ref[lo:hi];power=np.r_[0,np.cumsum(search**2)];summed=np.r_[0,np.cumsum(search)]
    var=(power[width:]-power[:-width])-(summed[width:]-summed[:-width])**2/width
    corr=signal.correlate(search,actual,mode='valid')/np.maximum(np.sqrt(np.maximum(var,0)*np.sum(actual**2)),1.e-9)
    at=int(np.argmax(corr));return round(float(corr[at]),3),round((lo+at)/100,3)

def analyze(folder):
    params=json.loads((folder/'windows.json').read_text())
    meter=np.atleast_2d(np.loadtxt(folder/'meter.csv',delimiter=',',skiprows=1))
    points=defaultdict(list);log=(folder/'profile/trace.log').read_text()
    for ts,t,c,ms in re.findall(r'(\d+) tracefin_T(\d+)_C(\d+)_M(\d+)',log):
        if t=='0':
            assert c=='0'  # Stopping the previous title clears its overlay.
            continue
        points[t].append((int(ts),int(c),int(ms)))
    assert 'traceallendsdone' in log and set(points)==set(params)
    result={}
    for t,p in params.items():
        tr=p['track'];end=p['end'];cue=p['cue']
        pts=points[t];vis=[r[2] for r in pts if r[1]==cue];after=[r[2] for r in pts if not r[1] and r[2]>=end]
        assert vis and after and max(vis)<end<=min(after) and end-max(vis)<=550 and min(after)-end<=550,(tr,vis,after)
        y,rate=sf.read(HERE.parent/'audio'/(tr+'.ogg'),dtype='float32',always_2d=True)
        n=rate//100
        ref=smooth(np.max(np.abs(y[:len(y)//n*n].reshape(-1,n*2)),axis=1).astype('float64'))
        start=pts[0][0]+680;stop=pts[-1][0]-300
        wins=[(start,stop),(start,(start+stop)//2),((start+stop)//2,stop)]
        scores=[]
        for a,b in wins:
            est=pts[0][2]/1000+(a-pts[0][0])/1000
            res=fit(ref,meter[:,0],meter[:,1],a,b,est)
            if res:
                r,sec=res
                diffs=[ms/1000-(sec+(q-a)/1000) for q,c,ms in pts if a<=q<=b]
                scores.append({'correlation':r,'reference_start':sec,'cursor_minus_audio_at_update_ms':round(float(np.median(diffs))*1000) if diffs else None,'sample_wall_ms':a})
        off_tick=next(q for q,c,ms in pts if c==0 and ms>=end)
        fits=[s for s in scores if s['correlation']>=.55] or [max(scores,key=lambda s:s['correlation'])]
        clear_errors=[round(1000*s['reference_start']+off_tick-s['sample_wall_ms']-end) for s in fits]
        result[tr]={'audio_minus_planned_at_clear_ms':round(float(np.median(clear_errors))),
                    'cue':cue,'planned_end_ms':end,'last_visible_ms':max(vis),'first_hidden_ms':min(after),'peak_vs_source':scores}
    return result
if __name__=='__main__':
    import sys
    folder=HERE/'runs'/(sys.argv[1] if len(sys.argv)>1 else 'final-song-ends');r=analyze(folder)
    (folder/'timing-result.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf8')
    for t,row in r.items():print(t,row['last_visible_ms'],row['first_hidden_ms'],[(s['correlation'],s['cursor_minus_audio_at_update_ms']) for s in row['peak_vs_source']])
