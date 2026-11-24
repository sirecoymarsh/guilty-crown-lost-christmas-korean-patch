"""음성 전사 결과를 정답 목록(ground_truth.json)과 대조해 정확도를 잰다.

받는 꼴(자동 판별):
- 폴더: 그 안의 *.txt(파일 하나에 음성 하나, 이름=음성 파일 이름) 또는 *.json/*.jsonl/*.csv/*.tsv
- *.json: {"lx02/0100010a02": "텍스트", …} 또는 [{…}, …]
- *.jsonl / *.csv / *.tsv: 줄마다 음성 키(voice·voice_id·file·path·name·id·audio·src)와 글(text·transcript·ja·japanese·result·stt)
음성 키는 'voice/LX02/0100010a02.ogg' · 'LX02\\0100010a02' · '0100010a02' 무엇이든 된다(이름만 오면 정답 쪽에서 유일하게 맞을 때만 짝짓는다).

지표: CER(글자 오류율) = 편집 거리 / 정답 길이.
- 읽기 CER: 양쪽을 히라가나 읽기로 바꾼 뒤(pykakasi) 문장부호를 빼고 비교 — 한자/가나 표기 차이를 무시한다.
- 표기 CER: NFKC·가타카나→히라가나만 맞추고 비교.
- 주 CER(cer): 줄마다 둘 중 낮은 값. 루비는 루비 읽기·본문 둘 다로 재서 가까운 쪽, 정답 꼴이 둘이면 가까운 쪽.
숨소리·비명만 있는 줄은 따로 집계한다. pooled_cer 은 전체 편집 수 / 전체 정답 글자 수다.

쓰는 법: python score_stt.py <전사 결과 경로> <ground_truth.json> <출력 폴더>
"""
import sys, re, json, csv, statistics, unicodedata, collections
from pathlib import Path
import jaconv, pykakasi
from rapidfuzz.distance import Levenshtein

KEY_FIELDS = ('voice_id', 'voice', 'file', 'path', 'name', 'id', 'audio', 'src', 'filename')
TEXT_FIELDS = ('text', 'transcript', 'transcription', 'ja', 'japanese', 'result', 'stt', 'output')
PUNCT = re.compile(r'[\s　「」『』《》（）()\[\]【】、。，．,.!?！？…‥―－—─~～・♪“”"\'’‘:：;；]')
NONLEX = re.compile(r'^[ぁぃぅぇぉあいうえおはひふへほっーんゃゅょアァイィウゥエェオォハヒフヘホッーンャュョ]*$')
kks = pykakasi.kakasi()


def key_of(raw):
    s = str(raw).replace('\\', '/').lower().strip()
    s = re.sub(r'\.(ogg|wav|mp3|flac|txt|json)$', '', s)
    s = s.split('voice/')[-1]
    parts = [p for p in s.split('/') if p]
    return '/'.join(parts[-2:]) if len(parts) >= 2 else parts[-1]


def load(path):
    p = Path(path); out = {}
    files = [p] if p.is_file() else sorted(x for x in p.rglob('*') if x.suffix.lower() in ('.txt', '.json', '.jsonl', '.csv', '.tsv'))
    per_file_txt = p.is_dir() and all(f.suffix.lower() == '.txt' for f in files)
    for f in files:
        suf = f.suffix.lower()
        if per_file_txt:
            out[key_of(f'{f.parent.name}/{f.stem}')] = f.read_text('utf-8-sig').strip(); continue
        if suf == '.json':
            d = json.loads(f.read_text('utf-8-sig'))
            if isinstance(d, dict) and all(isinstance(v, str) for v in d.values()):
                out.update({key_of(k): v for k, v in d.items()}); continue
            rows = d if isinstance(d, list) else d.get('rows') or d.get('items') or d.get('results') or []
        elif suf == '.jsonl':
            rows = [json.loads(l) for l in f.read_text('utf-8-sig').splitlines() if l.strip()]
        elif suf in ('.csv', '.tsv'):
            rows = list(csv.DictReader(f.read_text('utf-8-sig').splitlines(), delimiter='\t' if suf == '.tsv' else ','))
        else:
            continue
        for r in rows:
            k = next((r[x] for x in KEY_FIELDS if r.get(x)), None)
            t = next((r[x] for x in TEXT_FIELDS if isinstance(r.get(x), str)), None)
            if k is not None and t is not None: out[key_of(k)] = t
    return out


RUBY = re.compile(r'<RUBY TEXT="([^"]*)">([^<]*)</RUBY>')


def unruby(t, spoken):
    """루비는 성우가 루비를 읽었을 수도(spoken=True) 본문을 읽었을 수도 있다."""
    return RUBY.sub(lambda m: (m.group(1) or m.group(2)) if spoken else m.group(2), t)


def surface(t, spoken=False):
    return PUNCT.sub('', jaconv.kata2hira(unicodedata.normalize('NFKC', unruby(t, spoken))))


def reading(t, spoken=True):
    t = unicodedata.normalize('NFKC', unruby(t, spoken))
    return PUNCT.sub('', ''.join(x['hira'] for x in kks.convert(t)))


def cer(ref, hyp):
    return Levenshtein.distance(ref, hyp) / max(len(ref), 1)


def line_scores(ref_text, hyp):
    """(읽기 CER, 표기 CER, 주 CER, 쓴 읽기 정답). 루비 두 읽기 중 가까운 쪽, 주 CER 은 둘 중 낮은 값
    (pykakasi 가 전사의 한자를 잘못 읽어 생기는 가짜 오류를 막는다)."""
    hr = reading(hyp, True)
    cr, ref_r = min((cer(reading(ref_text, s), hr), reading(ref_text, s)) for s in (True, False))
    cs = min(cer(surface(ref_text, s), surface(hyp)) for s in (True, False))
    return cr, cs, min(cr, cs), ref_r


def main(stt_path, truth_path, outdir):
    truth = json.loads(Path(truth_path).read_text('utf-8'))['rows']
    stt = load(stt_path); out = Path(outdir); out.mkdir(parents=True, exist_ok=True)
    by_name = collections.defaultdict(list)
    for r in truth: by_name[r['voice_id'].split('/')[-1]].append(r['voice_id'])
    resolved = {}
    for k, v in stt.items():
        if '/' in k: resolved[k] = v
        elif len(by_name.get(k, [])) == 1: resolved[by_name[k][0]] = v
    rows = []; missing = []
    for r in truth:
        hyp = resolved.get(r['voice_id'])
        if hyp is None: missing.append(r['voice_id']); continue
        scored = [(line_scores(v['text'], hyp), v) for v in r['variants']]
        (cr, cs, c, ref_r), best = min(scored, key=lambda x: x[0][2])
        rows.append(dict(voice_id=r['voice_id'], file=best['file'], speaker=best['speaker'], source=best['source'],
                         truth=best['text'], stt=hyp, cer=round(c, 4), cer_reading=round(cr, 4), cer_surface=round(cs, 4),
                         ref_len=len(ref_r), edits=round(c * max(len(ref_r), 1)),
                         nonlexical=bool(NONLEX.match(surface(best['text']))), exact=c == 0))

    def summ(rs):
        if not rs: return None
        c = [x['cer'] for x in rs]
        pooled = sum(x['edits'] for x in rs) / max(sum(x['ref_len'] for x in rs), 1)
        return dict(lines=len(rs), pooled_cer=round(pooled, 4), mean_cer=round(statistics.mean(c), 4),
                    median_cer=round(statistics.median(c), 4),
                    mean_cer_reading=round(statistics.mean(x['cer_reading'] for x in rs), 4),
                    mean_cer_surface=round(statistics.mean(x['cer_surface'] for x in rs), 4),
                    exact=sum(x['exact'] for x in rs), over_20pct=sum(v > 0.2 for v in c))
    lex = [x for x in rows if not x['nonlexical']]; non = [x for x in rows if x['nonlexical']]
    per_speaker = {s: summ([x for x in lex if x['speaker'] == s]) for s in sorted({x['speaker'] or '?' for x in lex})}
    rep = dict(stt_source=str(stt_path), truth_voices=len(truth), stt_entries=len(stt), matched=len(rows),
               missing=missing, unresolved_keys=[k for k in stt if '/' not in k and len(by_name.get(k, [])) != 1][:50],
               lexical=summ(lex), nonlexical=summ(non), per_speaker_lexical=per_speaker,
               worst=sorted(rows, key=lambda x: -x['cer'])[:20])
    (out / 'stt_score.json').write_text(json.dumps(dict(rep, rows=rows), ensure_ascii=False, indent=2) + '\n', 'utf-8')
    print(json.dumps({k: v for k, v in rep.items() if k not in ('worst', 'rows')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    if len(sys.argv) != 4: raise SystemExit(__doc__)
    main(*sys.argv[1:])
