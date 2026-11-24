"""Resolve individual sustained-note boundaries that continuous accompaniment or backing vocals obscure."""
import csv,json,hashlib,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def run():
    base=json.loads((HERE/'source-cues.json').read_text(encoding='utf8'));rows=json.loads((HERE/'audit.json').read_text())
    v={r['id']:r for r in rows}
    # Repeated chorus entries and independent word landmarks distinguish these handoffs inside a sustained vocal.
    for left,t in [(187,75.4),(189,80.5),(190,84.9),(201,200.3)]:
        assert v[left]['track']==v[left+1]['track']=='lxbgm14'
        v[left]['new'][1]=v[left+1]['new'][0]=t
        for i in (left,left+1):v[i]['why'].append('reviewed chorus transition')
    # Light backing vocals remain in these gaps. Use the local release of the lead or the following verified lyric.
    ends={14:118.7,22:158.6,105:233.4,106:238.5,242:169.9,252:45.9,261:115.9,286:122.,330:166.6,335:185.3}
    for ident,t in ends.items():
        r=v[ident];r['new'][1]=min(t,v[ident+1]['new'][0]) if ident+1 in v and r['track']==v[ident+1]['track'] else t
        r['why'].append('reviewed lead release or next vocal entry')
    from release_timing import apply_releases
    apply_releases(rows)
    for row in rows:
        ident=row['id'];old=base['cues'][ident-1];assert old['id']==ident
        row['new']=[round(i,1) for i in row['new']]
        assert row['new'][1]-row['new'][0]>=.45
        if ident>1 and row['track']==v[ident-1]['track']:assert v[ident-1]['new'][1]<=row['new'][0],row
        old['start'],old['end']=[round(x*1000) for x in row['new']]
    (HERE/'accepted.json').write_text(json.dumps(base,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (HERE/'reviewed.json').write_text(json.dumps(rows,ensure_ascii=False,indent=1)+'\n',encoding='utf8')
    with (HERE/'줄별_타이밍.tsv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f,delimiter='\t');writer.writerow(('곡','자막 ID','기존 시작(초)','기존 끝(초)','수정 시작(초)','수정 끝(초)','원음 강제정렬 시작','원음 강제정렬 끝','보컬 강제정렬 시작','보컬 강제정렬 끝','검수 판정'))
        for r in rows:writer.writerow([r['track'],r['id'],*r['old'],*r['new'],*r['mix'],*r['vocals'],('보컬 경계 보정' if r['old']!=r['new'] else '유지')])
    for n in dict.fromkeys(row['track'] for row in rows):
        rr=[x for x in rows if x['track']==n];print(n,len(rr),sum(x['old']!=x['new'] for x in rr),sum(x['new'][1]>x['old'][1] for x in rr))
if __name__=='__main__':run()
