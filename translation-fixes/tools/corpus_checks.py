"""전체 번역에서 묶음을 가로지르는 기계 점검: 대사 속 그/그녀, 화자→청자 말 높이 분포.

쓰는 법: python corpus_checks.py <full_translation.json> <출력 json>
"""
import sys, json, re, collections
from pathlib import Path

TAG = re.compile(r'<[^>]*>|\{[^}]*\}')
QUOTE = re.compile(r'[「《](.*?)[」》]', re.S)
PRON = re.compile(r'(?<![가-힣])(그녀|그들|그는|그가|그를|그의|그에게|그한테|그와)(?![가-힣]*[만래럼런렇리])')


def level(sent):
    s = sent.strip().rstrip('!?…―~♪.').strip()
    if not s: return None
    if re.search(r'(습니다|습니까|십시오|ㅂ니다|입니다|입니까|십니까)$', s): return '합쇼'
    if re.search(r'(요|죠|세요|에요|예요|네요|군요|지요)$', s): return '해요'
    if re.search(r'(다|어|아|야|지|냐|니|자|라|래|게|군|네|걸|거든|잖아|구나|는데|해|와|가)$', s): return '반말'
    return None


def main(src, dst):
    units = json.loads(Path(src).read_text('utf-8-sig'))['units']
    pron = []; pairs = collections.defaultdict(lambda: collections.defaultdict(list))
    for u in units:
        ko = TAG.sub('', u['target']); c = u['context']
        for q in QUOTE.findall(ko):
            for m in PRON.finditer(q):
                pron.append(dict(id=u['id'], word=m.group(1), speaker=c.get('speaker'), ko=ko[:160]))
        if u['target'].lstrip().startswith(('「', '《')):
            sp = c.get('speaker') or '?'; ad = (c.get('addressee') or '?')[:20]
            for q in QUOTE.findall(ko):
                for sent in re.split(r'(?<=[.!?])\s+|\n', q):
                    lv = level(sent)
                    if lv: pairs[(sp, ad)][lv].append(u['id'])
    mixed = []
    for (sp, ad), d in pairs.items():
        total = sum(len(v) for v in d.values())
        if total < 6 or len(d) < 2: continue
        main_lv = max(d, key=lambda k: len(d[k]))
        minority = {k: v for k, v in d.items() if k != main_lv}
        share = sum(len(v) for v in minority.values()) / total
        if share >= 0.05:
            mixed.append(dict(speaker=sp, addressee=ad, total=total, main=main_lv,
                              counts={k: len(v) for k, v in d.items()},
                              minority_ids={k: sorted(set(v))[:15] for k, v in minority.items()}))
    mixed.sort(key=lambda x: -x['total'])
    out = dict(pronoun_in_dialogue=pron, speech_level_mixed_pairs=mixed)
    Path(dst).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print('pronoun hits', len(pron))
    for x in mixed[:25]: print(x['speaker'], '->', x['addressee'], x['counts'])


if __name__ == '__main__':
    if len(sys.argv) != 3: raise SystemExit(__doc__)
    main(*sys.argv[1:])
