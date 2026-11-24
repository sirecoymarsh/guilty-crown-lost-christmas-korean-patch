# Re-render ONE subtitle layer (cue 07) for mv_lx0201 with Codex's exact typesetting
# (prepare_subtitles_v2.py: GCLCKoreanSubtitle.ttf 134px, white fill, stroke 8 (0,0,0,240), anchor 'ms' at (1920,2040), 3840x2160 RGBA).
# Codex files are read only; all output goes to this work folder.
from pathlib import Path
import json, hashlib, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops
from fontTools.ttLib import TTFont
sys.stdout.reconfigure(encoding='utf-8')
W = Path(__file__).resolve().parents[1]
S = W / 'subtitles'; L = S / 'layers'; L.mkdir(parents=True, exist_ok=True)
CR = Path(r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\revisions\gemini-game-integration-20261026\movie-ruby\subtitles')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

meta = json.loads((CR / 'manifest.json').read_text(encoding='utf-8'))
fontpath = Path(meta['font']); assert sha(fontpath) == meta['font_sha256']
assert meta['font_size_4k'] == 134 and meta['stroke_4k'] == 8
for c in meta['cues']:
    assert sha(c['layer']) == c['sha256'], c['id']
font = ImageFont.truetype(str(fontpath), 134)
cmap = TTFont(fontpath).getBestCmap()

CID = '07'
OLD = '장단 좀 맞춰 줘, 개조 인간 1호.'
NEW = '장단 참 안 맞춰 주네, 개조인간 1호.'   # registry J00651 「장단 참 안 맞춰 주네, 개조인간 1호」 + movie trailing-period convention
c = next(x for x in meta['cues'] if x['id'] == CID)
assert c['text'] == OLD and c['layout'] == OLD and (c['first_frame'], c['last_frame']) == (622, 718)
assert all(ord(ch) in cmap for ch in NEW if not ch.isspace()), [ch for ch in NEW if ord(ch) not in cmap]

def render(lines):
    im = Image.new('RGBA', (3840, 2160)); d = ImageDraw.Draw(im)
    baseline = 2040 - (len(lines) - 1) * 160
    for i, s in enumerate(lines):
        d.text((1920, baseline + i * 160), s, font=font, fill='white', stroke_width=8, stroke_fill=(0, 0, 0, 240), anchor='ms')
    return im

# 1) Reproduction check: re-render the OLD text and compare to Codex's installed layer 07.png.
old_layer = Image.open(c['layer']).convert('RGBA')
rep = render([OLD])
diff = ImageChops.difference(rep, old_layer)
repro = {'old_layer': c['layer'], 'old_layer_sha256': c['sha256'], 'pixel_exact': diff.getbbox() is None,
         'max_channel_diff': max(b[1] for b in diff.getextrema()), 'diff_bbox': diff.getbbox()}
print('reproduction', repro)

# 2) Render NEW text. One line if it fits inside the same safe box the pipeline asserted (x 120..3720), else 2 lines (160px pitch).
lines = [NEW]
im = render(lines); bbox = im.getbbox()
if not (bbox[0] >= 120 and bbox[2] <= 3720):
    raise SystemExit(f'one line does not fit: {bbox}; choose a two-line break')
assert bbox[1] >= 1620 and bbox[3] <= 2080, bbox
p = L / f'{CID}.png'; im.save(p)
print('new layer', p, 'bbox', bbox, 'width', bbox[2] - bbox[0], 'old bbox', c['ink_bbox'], 'old width', c['ink_bbox'][2] - c['ink_bbox'][0])

# 3) Manifest / ASS / SRT for this revision (copies of Codex's 10-26 files with only cue 07 changed).
c.update(text=NEW, layout=NEW, layer=str(p), ink_bbox=list(bbox), sha256=sha(p), source_ids=c['source_ids'],
         registry_short_id='J00651', previous_text=OLD, previous_layer=repro['old_layer'], previous_layer_sha256=repro['old_layer_sha256'],
         semantic_editor='Claude (registry_1121 J00651)')
meta.update(status='ONE_CUE_REBURN_07', changed_cues=[CID], unchanged_layers_reused=17,
            source_manifest=str(CR / 'manifest.json'), source_manifest_sha256=sha(CR / 'manifest.json'),
            reproduction_check_old_text=repro, registry=r'F:\AI\gclx-4k\release_1121\registry_1121.json')
(S / 'manifest.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

ass = (CR / 'mv_lx0201.ko.ass').read_text('utf-8-sig')
needle = r'Dialogue: 0,0:00:20.75,0:00:23.99,KO,캐롤,0,0,0,,{\an2\pos(1920,2040)}' + OLD
assert ass.count(needle) == 1
ass = ass.replace(needle, needle[:-len(OLD)] + NEW)
(S / 'mv_lx0201.ko.ass').write_text(ass, encoding='utf-8-sig')
srt = (CR / 'mv_lx0201.ko.srt').read_text('utf-8-sig')
assert srt.count('00:00:20,754 --> 00:00:23,991\n' + OLD + '\n') == 1
srt = srt.replace(OLD, NEW)
(S / 'mv_lx0201.ko.srt').write_text(srt, encoding='utf-8-sig')
print('wrote manifest/ass/srt; layer sha256', c['sha256'])
