"""다른 세션이 남긴 frames.bin(프레임마다 벽시계 시각, double)을 따로 읽어 구간별 프레임 간격을 센다. 읽기만 한다.
python -X utf8 frames_gaps.py <시험 이름> [...]
"""
import json, struct, sys
from pathlib import Path

RUNS = Path(r'F:\AI\gclx-4k\testrun')


def load(name):
    run = RUNS / name
    rep = json.loads((run / 'report.json').read_text('utf-8'))
    b = (run / 'profile' / 'frames.bin').read_bytes()
    ts = struct.unpack('<%dd' % (len(b) // 8), b[:len(b) // 8 * 8])
    t0 = rep['t0_epoch']
    return rep, [t - t0 for t in ts]


def phase_stats(ts, a, b):
    seg = [t for t in ts if a <= t < b]
    if len(seg) < 2:
        return dict(n=len(seg))
    d = [y - x for x, y in zip(seg, seg[1:])]
    # 구간 앞뒤 끝의 빈 시간도 간격으로 친다(구간 안에 프레임이 아예 없던 시간)
    d = [seg[0] - a] + d + [b - seg[-1]]
    return dict(n=len(seg), fps=round(len(seg) / (b - a), 1), max=round(max(d), 2),
                over06=sum(1 for x in d if x > 0.6), over06_sum=round(sum(x for x in d if x > 0.6), 1),
                over025=sum(1 for x in d if x > 0.25), over025_sum=round(sum(x for x in d if x > 0.25), 1),
                over01=sum(1 for x in d if x > 0.1), over01_sum=round(sum(x for x in d if x > 0.1), 1))


def main():
    for name in sys.argv[1:]:
        rep, ts = load(name)
        clicks = [c[1] for c in rep.get('clicks_xy', [])]
        hovers = [h[1] for h in rep.get('hovers_xy', [])]
        end = ts[-1] if ts else 0
        print(f'=== {name}: frames={len(ts)} last={end:.1f}s clicks={clicks} hovers={len(hovers)} ({hovers[0] if hovers else None}~{hovers[-1] if hovers else None})')
        marks = [0.0] + clicks + ([hovers[0]] if hovers else []) + [end]
        marks = sorted(set(marks))
        names = {0: '시작~'}
        for a, b in zip(marks, marks[1:]):
            lab = '타이틀' if a == 0 else ('사운드 진입 뒤' if clicks and a == clicks[0] else ('재생 시작 뒤' if len(clicks) > 1 and a == clicks[1] else '올림 구간'))
            print(f'  {a:6.1f}~{b:6.1f} {lab:<8} {phase_stats(ts, a, b)}')
        # 올림 구간: 올림 사건마다 그 뒤 첫 큰 간격
        if hovers:
            seg = [t for t in ts if t >= hovers[0] - 0.5]
            gaps = [(x, y - x) for x, y in zip(seg, seg[1:]) if y - x > 0.25]
            print('  올림 구간 0.25초 넘는 간격(시작 시각:길이):', ' '.join(f'{x:.1f}:{g:.2f}' for x, g in gaps))


if __name__ == '__main__':
    main()
