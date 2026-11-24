"""Time the existing lyric text on both the game's mix and its vocal stem. Does not generate lyrics."""
from pathlib import Path
import os,re,json,sys,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
os.environ.update(TEMP=str(HERE),TMP=str(HERE),HF_HUB_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
dllpath=r'P:\AI\forge\venv\Lib\site-packages\torch\lib';os.environ['PATH']=dllpath+os.pathsep+os.environ['PATH'];dll=os.add_dll_directory(dllpath)
sys.path.insert(0,r'P:\AI\Codex\projects\sorairo_no_fuukin_ko\work\ui_video_integration_20260922\opening_final\stt_pkgs')
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from faster_whisper import WhisperModel
from faster_whisper.tokenizer import Tokenizer
from faster_whisper.audio import pad_or_trim
model=WhisperModel(r'P:\AI\Codex\projects\drakoi-korean\vocal-subtitles\tools\faster-whisper-large-v3',device='cuda',compute_type='float16',local_files_only=True)
def language(track,text):
    if re.search(r'[\u3040-\u30ff\u3400-\u9fff]',text):return 'ja'
    if track in ('lxbgm01','lxbgm18','lxbgm19'):return 'de'
    return 'en'
def groups(rows,maximum):
    g=[]
    for c in rows:
        if g and (c['end']-g[0]['start']>maximum or c['start']-g[-1]['end']>3500 or language(c['track'],c['source'])!=language(g[0]['track'],g[0]['source'])):
            yield g;g=[]
        g.append(c)
    if g:yield g
def align(track,src,rows,maximum):
    wave,sr=sf.read(src,dtype='float32',always_2d=True);wave=wave.mean(1)
    if sr==44100:wave=resample_poly(wave,160,441).astype('float32')
    else:assert sr==16000
    out=[]
    for g in groups(rows,maximum):
        # Clip at mid-gaps to avoid asking the model to align words from two different verses.
        start=max(0,g[0]['start']/1000-2);end=min(len(wave)/16000,g[-1]['end']/1000+2.3)
        clip=wave[round(start*16000):round(end*16000)]
        features=model.feature_extractor(clip)
        enc=model.encode(pad_or_trim(features));tok=Tokenizer(model.hf_tokenizer,True,task='transcribe',language=language(track,g[0]['source']))
        tokens=[];indices=[]
        for c in g:
            tt=tok.encode(' '+c['source']);indices.append((len(tokens),len(tokens)+len(tt)));tokens+=tt
        ar=model.model.align(enc,tok.sot_sequence,[tokens],features.shape[-1],median_filter_width=7)[0]
        pair=np.asarray(ar.alignments);jumps=np.r_[True,np.diff(pair[:,0])!=0]
        boundaries=pair[jumps,1]*.02+start;pr=ar.text_token_probs
        if len(boundaries)<len(tokens)+1:raise ValueError((track,len(boundaries),len(tokens)))
        for j,(c,(a,b)) in enumerate(zip(g,indices)):
            out.append({'id':c['id'],'s':round(float(boundaries[a]),3),'e':round(float(boundaries[b]),3),
                        'first_end':round(float(boundaries[min(a+1,b)]),3),'last_on':round(float(boundaries[max(a,b-1)]),3),
                        'prob':round(float(np.mean(pr[a:b])),3),'first':j==0,'last':j==len(g)-1})
    return out
rows=json.loads((ROOT/'data/lyrics.json').read_text(encoding='utf8'))['cues'];names=list(dict.fromkeys(c['track'] for c in rows));names.remove('lxbgm14');names.insert(0,'lxbgm14')
folder=HERE/'align';folder.mkdir(exist_ok=True)
for n in names:
    target=folder/(n+'.json')
    if target.exists():continue
    ref=HERE/'vocals'/(n+'.flac')
    if not ref.exists():raise FileNotFoundError(ref)
    rr=[c for c in rows if c['track']==n];t=time.time()
    res={'mix':align(n,ROOT/'audio'/(n+'.ogg'),rr,19000),'vocals':align(n,ref,rr,22500)}
    target.write_text(json.dumps(res,indent=1),encoding='utf8')
    print(n,len(rr),round(time.time()-t,1),flush=True)
