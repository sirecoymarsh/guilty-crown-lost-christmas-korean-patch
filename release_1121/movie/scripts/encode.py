# Re-encode mv_lx0201 (4K mp4 + native ngs) with Codex's exact 10-26 command (movie-ruby/final/command.json),
# changing only: cue 07 layer -> this folder's new layer, audio source -> currently installed .ngs (MP2 packets copied),
# filter/output/progress paths -> this work folder. Codex folder and game folder are read only.
from pathlib import Path
import json, os, sys, time, subprocess, hashlib
sys.stdout.reconfigure(encoding='utf-8')
W = Path(__file__).resolve().parents[1]
O = W / 'out'; G = W / 'logs'; T = W / 'tmp'
CF = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\gemini-game-integration-20261026\movie-ruby\final')
INSTALLED_NGS = Path(r'P:\AI\gclx-codexrun\game\dx\mv_lx0201.ngs')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

prior = json.loads((CF / 'command.json').read_text(encoding='utf-8'))
args = list(prior['args'])
meta = json.loads((W / 'subtitles' / 'manifest.json').read_text(encoding='utf-8'))
cues = meta['cues']; assert len(cues) == 18 and meta['changed_cues'] == ['07']

# Layer inputs in Codex's order must be exactly the manifest cues; replace only 07.
layer_pos = [i for i, a in enumerate(args) if a.lower().endswith('.png')]
assert len(layer_pos) == 18 and all(args[i - 1] == '-i' for i in layer_pos)
for i, c in zip(layer_pos, cues):
    assert sha(c['layer']) == c['sha256'], c['id']
    if c['id'] == '07':
        assert args[i].endswith(r'subtitles-v2\layers\07.png'); args[i] = c['layer']
    else:
        assert args[i] == c['layer'], (c['id'], args[i], c['layer'])

base = args[args.index('-i') + 1]
assert base.endswith(r'clean-base-v2\clean-native-ffv1.mkv')
assert sha(base) == '8fdb52a0b7538d5c72ba67625e34da8becd5ab200e515061ee05ebc0e7899079'

# audio source (input 19)
ai = [i for i, a in enumerate(args) if a.endswith(r'game\dx\mv_lx0201.ngs')]; assert len(ai) == 1
args[ai[0]] = str(INSTALLED_NGS)
assert args[args.index('[sd]') + 1:args.index('[sd]') + 3] == ['-map', '19:a:0']

# filter script: same graph as Codex's (layer indices unchanged)
filt = (CF / 'filter.txt').read_text()
fp = O / 'filter.txt'; fp.write_text(filt)
k = args.index('-filter_complex_script'); args[k + 1] = str(fp)

# outputs
mp4 = O / 'mv_lx0201.mp4'; ngs = O / 'mv_lx0201.ngs'; prog = G / 'progress.txt'
for p in (mp4, ngs, prog):
    if p.exists(): p.unlink()
k = [i for i, a in enumerate(args) if a.endswith(r'final\mv_lx0201.mp4')]; assert len(k) == 1; args[k[0]] = str(mp4)
k = [i for i, a in enumerate(args) if a.endswith(r'final\mv_lx0201.ngs')]; assert len(k) == 1; args[k[0]] = str(ngs)
k = args.index('-progress'); args[k + 1] = str(prog)
assert all(a.startswith(str(W)) for a in (args[args.index('-progress') + 1], args[args.index('-filter_complex_script') + 1], str(mp4), str(ngs)))

# Show the diff of arguments vs Codex's command
changes = [(i, a, b) for i, (a, b) in enumerate(zip(prior['args'], args)) if a != b]
assert len(args) == len(prior['args'])
env = dict(os.environ, TEMP=str(T), TMP=str(T))
(G / 'command.json').write_text(json.dumps({'args': args, 'changed_vs_codex_20261026': changes, 'codex_command': str(CF / 'command.json'),
    'overlay_n_origin': prior['overlay_n_origin'], 'expected_video_frames': 1858}, ensure_ascii=False, indent=2), encoding='utf-8')
for i, a, b in changes: print('arg', i, ':', a, '->', b)
t = time.monotonic()
with (G / 'encode.log').open('wb') as log:
    p = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=log, stdin=subprocess.DEVNULL, env=env, cwd=str(T),
                         creationflags=subprocess.CREATE_NO_WINDOW)
    code = p.wait()
res = {'exit_code': code, 'seconds': round(time.monotonic() - t, 1),
       'files': {x.name: {'bytes': x.stat().st_size, 'sha256': sha(x)} for x in (mp4, ngs) if x.exists()}}
(G / 'encode.json').write_text(json.dumps(res, indent=2), encoding='utf-8')
print(json.dumps(res, indent=2)); sys.exit(code)
