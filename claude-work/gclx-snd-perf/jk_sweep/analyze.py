"""jk_sweep 결과 풀이: J/K 누름마다 장면·DLL 결정(bgmkeep.log)·소리 끊김(최고값 1e-4 미만 연속 길이)을 한 줄로.
python -X utf8 analyze.py <이름 앞머리> → F:\AI\gclx-4k\testrun\<앞머리>_summary.json
"""
import json, re, sys
from pathlib import Path
RUNS = Path(r'F:\AI\gclx-4k\testrun')
pre = sys.argv[1]
SIL = 1e-4
allrows = []
for d in sorted(RUNS.glob(f'{pre}_lx*')):
    if not d.is_dir(): continue
    rep = json.loads((d / 'report.json').read_text('utf-8'))
    ap = json.loads((d / 'audio_peaks.json').read_text('utf-8')) if (d / 'audio_peaks.json').exists() else None
    if not isinstance(ap, dict): print(d.name, 'no audio'); continue
    t2e = lambda tick: ap['ep0'] + (int(tick) - ap['tick0']) / 1000.0
    bk = []
    p = d / 'profile/bgmkeep.log'
    if p.exists():
        for l in p.read_text('cp932', 'replace').splitlines():
            m = re.match(r'(\d+) (.*)', l)
            if m: bk.append((t2e(m.group(1)), m.group(2)))
    tr = []
    p = d / 'profile/trace.log'
    if p.exists():
        for l in p.read_text('cp932', 'replace').splitlines():
            m = re.match(r'(\d+) (\S+) ?(.*)', l)
            if m: tr.append((t2e(m.group(1)), m.group(3)))
    S = ap['samples']
    for ka, sec in rep.get('keys_at', []):
        if not ka.split(':')[1].lower() in ('0x4a', '0x4b'): continue
        t = rep['t0_epoch'] + sec
        scene = [g for (e, g) in tr if e <= t]
        sc = scene[-1] if scene else '?'
        nline = sum(1 for (e, g) in tr if e <= t and g == sc)
        ev = [s for (e, s) in bk if t - 0.2 <= e <= t + 6]
        before = [v for (e, v) in S if t - 1.0 <= e < t]
        after = [(e, v) for (e, v) in S if t <= e < t + 5]
        run = best = 0.0; last = None
        for e, v in after:
            if v < SIL:
                if last is not None: run += e - last
                best = max(best, run)
            else:
                run = 0.0
            last = e
        kept = [s for s in ev if s.startswith('keep ')]
        aft = [s for s in ev if s.startswith('after ')]
        diff = [s for s in ev if s.strip().startswith('diff ')]
        row = {'run': d.name, 'sec': sec, 'key': 'J' if ka.endswith('4A') else 'K', 'scene': sc, 'line': nline,
               'pre_peak': round(max(before), 4) if before else None, 'silence_s': round(best, 2),
               'keep': kept, 'after': aft, 'diff': diff}
        allrows.append(row)
        flag = ''
        if any('same=1' in a for a in aft): flag = 'KEPT'
        elif aft: flag = 'MISMATCH'
        elif any('keep none' in k for k in kept): flag = 'NONE'
        elif not ev: flag = 'NOLOG'
        row['flag'] = flag
        print(f"{d.name:14} {sec:6.1f} {row['key']} {sc:14} L{nline:<4} pre={row['pre_peak']} sil={best:4.2f}s {flag:8} {(kept[0] if kept else '')[:90]}")
        for x in aft + diff: print('      ', x[:200])
(RUNS / f'{pre}_summary.json').write_text(json.dumps(allrows, ensure_ascii=False, indent=1), 'utf-8')
from collections import Counter
print(Counter(r['flag'] for r in allrows), 'silence>=0.5s:', sum(1 for r in allrows if r['silence_s'] >= 0.5),
      'of which KEPT:', sum(1 for r in allrows if r['silence_s'] >= 0.5 and r['flag'] == 'KEPT'))
