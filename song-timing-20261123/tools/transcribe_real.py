import os,sys,json,time,dataclasses,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.update(TEMP=str(ROOT/'temp'),TMP=str(ROOT/'temp'),PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1')
sys.path.insert(0,str(ROOT/'tools'))
from npa_adapter import NPA
arc=NPA(r'P:\AI\gclx-codexrun\game\sound.npa')
tracks={'lxbgm19':'de'}
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
models=[('turbo',r'P:\AI\Codex\projects\fatal-twelve-ko\opening_localization_20261002\tools\model_cache\models--mobiuslabsgmbh--faster-whisper-large-v3-turbo\snapshots\0a363e9161cbc7ed1431c9597a8ceaf0c4f78fcf'),('large',r'P:\AI\Codex\projects\drakoi-korean\vocal-subtitles\tools\faster-whisper-large-v3')]
for mid,mpath in models:
 print('loading',mid,flush=True)
 m=WhisperModel(mpath,device='cuda',compute_type='float16',local_files_only=True)
 for name,lang in tracks.items():
  dst=ROOT/'data'/f'{name}.{mid}.json'
  if dst.exists():continue
  t=time.time(); print('start',mid,name,flush=True)
  segs,info=m.transcribe(str(ROOT/'audio'/(name+'.ogg')),language=lang,task='transcribe',word_timestamps=True,beam_size=5,condition_on_previous_text=False,vad_filter=False,hallucination_silence_threshold=2)
  rows=[dataclasses.asdict(s) for s in segs]
  dst.write_text(json.dumps({'source':'user game sound.npa','audio_sha256':hashlib.sha256((ROOT/'audio'/(name+'.ogg')).read_bytes()).hexdigest(),'model':mpath,'language':lang,'task':'transcribe','duration':info.duration,'segments':rows,'seconds':time.time()-t},ensure_ascii=False,indent=2),encoding='utf-8')
  print('done',mid,name,round(time.time()-t,1),len(rows),flush=True)
 del m
