import os,sys,json,time,dataclasses,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(TEMP=str(ROOT/'temp'),TMP=str(ROOT/'temp'),PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1')
sys.path.insert(0,str(ROOT/'tools'))
from npa_adapter import NPA
arc=NPA(r'P:\AI\gclx-codexrun\game\sound.npa')
tracks={'lxsong02':'ja'}
for e in arc.entries:
 name=Path(e['name'].replace('\\','/')).stem
 if name in tracks:
  p=ROOT/'audio'/(name+'.ogg')
  if not p.exists():p.write_bytes(arc.read(e))
print('audio extracted',len(tracks),flush=True)
lib=r'P:\AI\forge\venv\Lib\site-packages\torch\lib'
os.environ['PATH']=lib+os.pathsep+os.environ['PATH'];os.add_dll_directory(lib)
sys.path.insert(0,r'P:\AI\Codex\projects\sorairo_no_fuukin_ko\work\ui_video_integration_20260922\opening_final\stt_pkgs')
from faster_whisper import WhisperModel
models=[('turbo-ja',r'P:\AI\Codex\projects\fatal-twelve-ko\opening_localization_20261002\tools\model_cache\models--mobiuslabsgmbh--faster-whisper-large-v3-turbo\snapshots\0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf'),('large-ja',r'P:\AI\Codex\projects\drakoi-korean\vocal-subtitles\tools\faster-whisper-large-v3')]

from faster_whisper.audio import decode_audio
m=WhisperModel(models[-1][1],device='cuda',compute_type='float16',local_files_only=True)
for name,start,end,lang in [('lxsong02',204,216,'en')]:
 x=decode_audio(str(ROOT/'audio'/(name+'.ogg')))[int(start*16000):int(end*16000)]
 segs,info=m.transcribe(x,language=lang,task='transcribe',word_timestamps=True,beam_size=5,condition_on_previous_text=False,vad_filter=False)
 rows=[dataclasses.asdict(v) for v in segs]
 for v in rows:v['start']+=start;v['end']+=start
 (ROOT/'data'/f'{name}.outro-en.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),'utf-8')
 print(name,[(v['start'],v['end'],v['text']) for v in rows],flush=True)
