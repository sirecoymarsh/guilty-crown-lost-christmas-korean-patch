# Verify the re-burned mv_lx0201 against the currently installed files (read only).
# - frame count / continuity (showinfo), per-frame PSNR/MSE vs installed (which frames changed)
# - MP2 audio packets: byte-identical stream + identical per-packet pts/size/md5 (framemd5, stream copy)
# - sample frames (inside the changed cue and in unchanged neighbour cues) as PNG for visual review
from pathlib import Path
import json, os, re, sys, subprocess, hashlib
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
W = Path(__file__).resolve().parents[1]; V = W / 'verify'; V.mkdir(exist_ok=True); T = W / 'tmp'
FF = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\vendor\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
INST = {'native': Path(r'P:\AI\gclx-codexrun\game\dx\mv_lx0201.ngs'), '4k': Path(r'P:\AI\gclx-codexrun\game\dx4k\mv_lx0201.mp4')}
NEW = {'native': W / 'out' / 'mv_lx0201.ngs', '4k': W / 'out' / 'mv_lx0201.mp4'}
SIZE = {'native': (1024, 576), '4k': (3840, 2160)}
CUE = (622, 718)
SAMPLES = {'f0659_cue07_22.0s': 659, 'f0640_cue07_start': 640, 'f0750_cue08_neighbour': 750, 'f0600_cue06_neighbour': 600}
env = dict(os.environ, TEMP=str(T), TMP=str(T))
def run(cmd, log=None, capture=False):
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, env=env, cwd=str(T), creationflags=subprocess.CREATE_NO_WINDOW)
    if log: Path(log).write_bytes(r.stderr)
    assert r.returncode == 0, (cmd, r.stderr[-2000:])
    return r
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def compare(label):
    d = V / label; d.mkdir(exist_ok=True)
    stats = d / 'psnr.log'
    # showinfo on the new file, psnr new vs installed (stats_file path relative to cwd: use forward slashes + escaping)
    sp = str(stats).replace('\\', '/').replace(':', '\\:')
    cmd = [FF, '-hide_banner', '-loglevel', 'info', '-nostdin', '-threads', '8', '-i', str(NEW[label]), '-threads', '8', '-i', str(INST[label]),
           '-lavfi', f"[0:v:0]showinfo[a];[a][1:v:0]psnr=stats_file='{sp}'", '-an', '-f', 'null', '-']
    run(cmd, log=d / 'decode-compare.log')
    logs = (d / 'decode-compare.log').read_text(errors='replace')
    pairs = [(int(a), float(b)) for a, b in re.findall(r'\bn:\s*(\d+)\s+pts:\s*-?\d+\s+pts_time:([0-9.eE+-]+)', logs)]
    ns = [a for a, b in pairs]; pts = [b for a, b in pairs]
    err = max(abs((v - pts[0]) - i * 1001 / 30000) for i, v in enumerate(pts))
    bad = [l for l in logs.splitlines() if re.search(r'error|corrupt|invalid|concealing', l, re.I)]
    rows = []
    for line in stats.read_text().splitlines():
        kv = dict(x.split(':', 1) for x in line.split())
        rows.append((int(kv['n']) - 1, float(kv['mse_avg']), kv['psnr_avg']))
    changed = [n for n, mse, _ in rows if mse > 0]
    outside = [(n, mse, p) for n, mse, p in rows if mse > 0 and not (CUE[0] <= n <= CUE[1])]
    inside_unchanged = [n for n, mse, _ in rows if mse == 0 and CUE[0] <= n <= CUE[1]]
    def fl(p): return float('inf') if p == 'inf' else float(p)
    res = {'new_file': str(NEW[label]), 'installed_file': str(INST[label]), 'new_sha256': sha(NEW[label]), 'installed_sha256': sha(INST[label]),
           'frames_new': len(pairs), 'frame_index_sequence_ok': ns == list(range(len(ns))), 'pts_strictly_increasing': all(b > a for a, b in zip(pts, pts[1:])),
           'max_cfr_timing_error_s': err, 'psnr_rows': len(rows), 'decode_error_lines': bad[:10],
           'changed_frames_count': len(changed), 'changed_range': [min(changed), max(changed)] if changed else None,
           'changed_frames_outside_cue07': len(outside), 'outside_ranges': ranges([n for n, _, _ in outside]),
           'outside_min_psnr_db': min((fl(p) for _, _, p in outside), default=None),
           'cue07_frames_identical_to_installed': inside_unchanged,
           'identical_frames_count': sum(1 for _, mse, _ in rows if mse == 0)}
    return res

def ranges(ns):
    out = []
    for n in ns:
        if out and n == out[-1][1] + 1: out[-1][1] = n
        else: out.append([n, n])
    return out

def frames(label, which):
    d = V / 'frames'; d.mkdir(exist_ok=True)
    src = NEW[label] if which == 'new' else INST[label]
    sel = '+'.join(f'eq(n\\,{n})' for n in sorted(SAMPLES.values()))
    tmpl = d / f'{label}-{which}-%02d.png'
    run([FF, '-hide_banner', '-loglevel', 'error', '-nostdin', '-i', str(src), '-map', '0:v:0', '-an', '-vf', f"select='{sel}'", '-fps_mode', 'vfr', str(tmpl)])
    names = {}
    for i, (name, n) in enumerate(sorted(SAMPLES.items(), key=lambda x: x[1]), 1):
        p = d / f'{label}-{which}-{i:02d}.png'; q = d / f'{label}-{which}-{name}.png'
        if q.exists(): q.unlink()
        p.rename(q); names[name] = str(q)
        assert Image.open(q).size == SIZE[label]
    return names

def audio():
    out = {}
    for k, p in (('new', NEW['native']), ('installed', INST['native'])):
        r = run([FF, '-hide_banner', '-loglevel', 'error', '-nostdin', '-i', str(p), '-map', '0:a:0', '-c:a', 'copy', '-vn', '-f', 'mp2', 'pipe:1'])
        f = run([FF, '-hide_banner', '-loglevel', 'error', '-nostdin', '-i', str(p), '-map', '0:a:0', '-c:a', 'copy', '-f', 'framemd5', 'pipe:1'])
        pk = [l for l in f.stdout.decode().splitlines() if l and not l.startswith('#')]
        (V / f'audio-framemd5-{k}.txt').write_bytes(f.stdout)
        v = run([FF, '-hide_banner', '-loglevel', 'error', '-nostdin', '-i', str(p), '-map', '0:v:0', '-c:v', 'copy', '-f', 'framemd5', 'pipe:1'])
        vp = [l.split(',')[1:4] for l in v.stdout.decode().splitlines() if l and not l.startswith('#')]  # dts, pts, duration
        (V / f'video-packets-framemd5-{k}.txt').write_bytes(v.stdout)
        out[k] = {'audio_sha256': hashlib.sha256(r.stdout).hexdigest(), 'audio_bytes': len(r.stdout), 'audio_packets': len(pk), 'packet_lines': pk,
                  'video_packets': len(vp), 'video_ts': vp}
    a, b = out['new'], out['installed']
    return {'new_audio_sha256': a['audio_sha256'], 'installed_audio_sha256': b['audio_sha256'], 'audio_bytes': a['audio_bytes'],
            'audio_stream_identical': a['audio_sha256'] == b['audio_sha256'], 'audio_packets': [a['audio_packets'], b['audio_packets']],
            'audio_packet_pts_size_md5_identical': a['packet_lines'] == b['packet_lines'],
            'expected_codex_audio_sha256': '89cbe10085be52099e92bfce8fa42ffeda9e4f7b8e2f62bf5ab685e90322d9f2',
            'video_packets': [a['video_packets'], b['video_packets']], 'video_packet_dts_pts_duration_identical': a['video_ts'] == b['video_ts']}

with ThreadPoolExecutor(6) as ex:
    fc = {k: ex.submit(compare, k) for k in ('native', '4k')}
    ff = {(k, w): ex.submit(frames, k, w) for k in ('native', '4k') for w in ('new', 'installed')}
    fa = ex.submit(audio)
    proof = {'compare': {k: f.result() for k, f in fc.items()}, 'audio_and_timestamps': fa.result(),
             'frames': {f'{k}-{w}': f.result() for (k, w), f in ff.items()}}

# sample-frame pixel differences new vs installed
fd = {}
for k in ('native', '4k'):
    for name in SAMPLES:
        a = np.asarray(Image.open(proof['frames'][f'{k}-new'][name]).convert('RGB')).astype(int)
        b = np.asarray(Image.open(proof['frames'][f'{k}-installed'][name]).convert('RGB')).astype(int)
        dd = np.abs(a - b).max(axis=2)
        ys, xs = np.nonzero(dd > 8)
        fd[f'{k}:{name}'] = {'identical': bool((dd == 0).all()), 'max_diff': int(dd.max()), 'pixels_diff_gt8': int((dd > 8).sum()),
                             'bbox_diff_gt8': [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None,
                             'mean_abs_diff': float(np.abs(a - b).mean())}
proof['sample_frame_diffs'] = fd
p = proof['audio_and_timestamps']
proof['summary'] = {
    'native_frames': proof['compare']['native']['frames_new'], '4k_frames': proof['compare']['4k']['frames_new'],
    'progress_dup_drop': open(W / 'logs' / 'progress.txt').read().strip().splitlines()[-3:],
    'audio_identical': p['audio_stream_identical'] and p['audio_packet_pts_size_md5_identical'] and p['new_audio_sha256'] == p['expected_codex_audio_sha256']}
(V / 'proof.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2), encoding='utf-8')
for k, v in proof['compare'].items(): print(k, json.dumps(v, ensure_ascii=False))
print('audio', json.dumps(p, ensure_ascii=False))
for k, v in fd.items(): print(k, v)
print(proof['summary'])
