import json, sys
sys.path.insert(0, r'F:/AI/gclx-4k/release_1121/qa')
from analyze_bl import presents, RUNS, Q
for run in sys.argv[1:]:
    r=json.load(open(RUNS/run/'report.json',encoding='utf-8')); t0=r['t0_epoch']; ev=r['events']
    ts=presents(Q/f'pm_{run}.csv'); off=round((ts[0]-t0)/3600)*3600; ts=[t-off for t in ts]
    print(run)
    for i,(n,t) in enumerate(ev):
        nxt=ev[i+1][1] if i+1<len(ev) else t+5
        seg=[x for x in ts if t<=x<min(nxt,t+5)]
        if not seg: print('   %-10s %6.1fs  no present'%(n,t-t0)); continue
        g=[(b-a)*1000 for a,b in zip(seg,seg[1:])]
        burst_end=seg[0]
        for a,b in zip(seg,seg[1:]):
            if b-a>0.2: break
            burst_end=b
        print('   %-10s %6.1fs  first %5.0fms  frames %3d  burst %5.0fms  max_gap_in_burst %4.0fms'%(n,t-t0,(seg[0]-t)*1000,len(seg),(burst_end-seg[0])*1000,max([x for x in g if x<=200] or [0])))
