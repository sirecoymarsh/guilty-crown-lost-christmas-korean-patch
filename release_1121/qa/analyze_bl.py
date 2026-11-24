import csv, datetime, json, sys
from pathlib import Path
RUNS=Path(r'F:/AI/gclx-4k/testrun'); Q=Path(r'F:/AI/gclx-4k/release_1121/qa')
def presents(p):
    out=[]
    for r in csv.DictReader(open(p,encoding='utf-8-sig')):
        s=r.get('TimeInDateTime','').strip()
        if not s: continue
        d,frac=(s.split('.')+['0'])[:2]
        t=datetime.datetime.strptime(d,'%Y-%m-%d %H:%M:%S').timestamp()+float('0.'+frac)
        out.append(t)
    return sorted(out)
def win(ts,a,b):
    seg=[t for t in ts if a<=t<=b]; g=[(y-x)*1000 for x,y in zip(seg,seg[1:])]
    if len(seg)<2: return None
    return dict(fps=round(len(seg)/(b-a)),first_ms=round((seg[0]-a)*1000),max_gap=round(max(g)),over50=sum(x>50 for x in g),over100=sum(x>100 for x in g),stall_ms=round(sum(x for x in g if x>50)))
for run in sys.argv[1:]:
    r=json.load(open(RUNS/run/'report.json',encoding='utf-8')); t0=r['t0_epoch']; ev=r['events']
    ts=presents(Q/f'pm_{run}.csv'); off=round((ts[0]-t0)/3600)*3600; ts=[t-off for t in ts]
    up=[t for n,t in ev if n=='wheel_up']; dn=[t for n,t in ev if n=='wheel_down']; ck=[t for n,t in ev if n=='click']
    s1=[t for t in up if t-t0<130]; s2=[t for t in up if t-t0>=130]
    print(run, 'presents',len(ts),'span',round(ts[0]-t0,1),round(ts[-1]-t0,1),'offset_h',off/3600)
    rows={'reading 95-105s':win(ts,t0+95,t0+105),'open (1st wheel +3s)':win(ts,s1[0],s1[0]+3),'scroll (wheels 2-10)':win(ts,s1[1],s1[-1]+0.7),
          'close (wheel down)':win(ts,dn[0],dn[-1]+2),'reopen +3s':win(ts,s2[0],s2[0]+3),'jump click +5s':win(ts,ck[0],ck[0]+5) if ck else None}
    for k,v in rows.items(): print('   %-22s'%k, v)
    # biggest gaps overall after 110s
    seg=[t for t in ts if t>t0+110]; gaps=sorted(((y-x)*1000,x-t0) for x,y in zip(seg,seg[1:]))[-5:]
    print('   top gaps after 110s (ms, at s):',[(round(g),round(a,1)) for g,a in gaps])
    print('   events:',[(n,round(t-t0,1)) for n,t in ev][:4],'...',[(n,round(t-t0,1)) for n,t in ev][-3:])
