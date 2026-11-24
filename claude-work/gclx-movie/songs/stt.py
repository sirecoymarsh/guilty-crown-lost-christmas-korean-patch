"""엔딩 노래 두 곡의 가사를 받아 적어(코덱스가 쓰던 로컬 faster-whisper large-v3) 곡 이름을 가린다.
ISOLATION(이토 카나코)·Where am I？(VERTUEUX) — 가사에 곡 이름이 들리는지, 어떤 말로 부르는지.
python -I -X utf8 stt.py"""
import sys, subprocess
from pathlib import Path
sys.path.insert(0, r'P:\AI\Codex\projects\sorairo_no_fuukin_ko\work\ui_video_integration_20260922\opening_final\stt_pkgs')
from faster_whisper import WhisperModel
FF = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\vendor\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
H = Path(__file__).parent
model = WhisperModel(r'P:\AI\Codex\projects\drakoi-korean\vocal-subtitles\tools\faster-whisper-large-v3', device='cpu', compute_type='int8', cpu_threads=8, local_files_only=True)
for name in ('lxsong01', 'lxsong02'):
    wav = H / f'{name}.wav'
    subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(H / f'{name}.ogg'), '-ac', '1', '-ar', '16000', str(wav)], check=True)
    segs, info = model.transcribe(str(wav), task='transcribe', beam_size=5, condition_on_previous_text=False, vad_filter=True, temperature=0)
    text = ' / '.join(s.text.strip() for s in segs)
    print('=====', name, 'lang', info.language, round(info.language_probability, 2))
    print(text[:1500], flush=True)
