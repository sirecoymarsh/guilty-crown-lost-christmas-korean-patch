# Compare every burned-in Korean cue of mv_lx0201 with the final registry (registry_1121.json).
# Read-only on Codex files; writes verify/registry-check.json in this work folder.
from pathlib import Path
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
W = Path(__file__).resolve().parents[1]
REG = Path(r'F:\AI\gclx-4k\release_1121\registry_1121.json')
CODEX = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\gemini-game-integration-20261026\movie-ruby\subtitles\manifest.json')
which = sys.argv[1] if len(sys.argv) > 1 else 'codex'
man = CODEX if which == 'codex' else W / 'subtitles' / 'manifest.json'
reg = json.loads(REG.read_text(encoding='utf-8'))
units = {u['short_id']: u for u in reg['units']}
lx = [u for u in reg['units'] if u['file'] == 'lx0201.nss' and u['lane'] == 'SetBacklog_raw_history']
assert [u['short_id'] for u in lx] == [f'J{n:05d}' for n in range(644, 663)], [u['short_id'] for u in lx]
groups = {'01': [644], '02': [645], '03': [646], '04': [647], '05a': [648], '05b': [649], '06': [650], '07': [651],
          '08': [652], '09': [653], '10': [654], '11': [655, 656], '12': [657], '13': [658], '14': [659],
          '15a': [660], '15b': [661], '16': [662]}

def norm(s):
    s = s.replace('「', '').replace('」', '').strip().strip('\u3000').strip()
    return s

def movie_form(parts):
    t = ' '.join(norm(p) for p in parts)
    if t and t[-1] not in '.?!…':
        t += '.'
    return t

cues = json.loads(man.read_text(encoding='utf-8'))['cues']
rows = []
for c in cues:
    ids = [f'J{n:05d}' for n in groups[c['id']]]
    us = [units[i] for i in ids]
    exp = movie_form([u['target_display'] for u in us])
    spk = us[0]['speaker']
    shown = c['text']
    row = {'cue': c['id'], 'short_ids': ids, 'frames': [c['first_frame'], c['last_frame']], 'speaker_movie': c['speaker'],
           'speaker_registry': spk, 'movie_text': shown, 'registry_movie_form': exp,
           'registry_target_display': [u['target_display'] for u in us], 'match': shown == exp and c['speaker'] == spk}
    if c.get('reading_text'):
        row['movie_ruby'] = {'base': c.get('ruby_base'), 'reading': c.get('reading_text')}
    rows.append(row)
mism = [r for r in rows if not r['match']]
out = {'manifest': str(man), 'registry': str(REG), 'cues': len(rows), 'matches': len(rows) - len(mism),
       'mismatches': [r['cue'] for r in mism], 'rows': rows}
(W / 'verify').mkdir(exist_ok=True)
(W / 'verify' / f'registry-check-{which}.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for r in rows:
    print(('OK  ' if r['match'] else 'DIFF'), r['cue'], r['short_ids'], repr(r['movie_text']), '' if r['match'] else '<> ' + repr(r['registry_movie_form']), r.get('movie_ruby', ''))
print('matches', out['matches'], '/', out['cues'], 'mismatches', out['mismatches'])
