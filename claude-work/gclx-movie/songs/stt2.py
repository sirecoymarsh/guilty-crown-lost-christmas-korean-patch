import sys
sys.path.insert(0, r'P:\AI\Codex\projects\sorairo_no_fuukin_ko\work\ui_video_integration_20260922\opening_final\stt_pkgs')
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
model = WhisperModel(r'P:\AI\Codex\projects\drakoi-korean\vocal-subtitles\tools\faster-whisper-large-v3', device='cpu', compute_type='int8', cpu_threads=8, local_files_only=True)
for name in ('lxsong01', 'lxsong02'):
    a = decode_audio(f'{name}.wav', sampling_rate=16000)
    for lang in ('ja', 'en'):
        segs, info = model.transcribe(a[16000 * 20:16000 * 140], language=lang, task='transcribe', beam_size=5, condition_on_previous_text=False, vad_filter=False, temperature=0, no_speech_threshold=0.95)
        print('=====', name, lang, ' / '.join(s.text.strip() for s in segs)[:700], flush=True)
