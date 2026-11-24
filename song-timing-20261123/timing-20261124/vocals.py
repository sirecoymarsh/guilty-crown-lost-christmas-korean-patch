from pathlib import Path
import sys,os,hashlib,json,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
TOOLS=Path(r'P:\AI\Codex\projects\drakoi-korean\vocal-subtitles\tools')
sys.path.insert(0,str(TOOLS/'separation_pkgs'))
dll=os.add_dll_directory(r'P:\AI\forge\venv\Lib\site-packages\torch\lib')
os.environ.update(TORCH_HOME=str(TOOLS/'torch-models'),TEMP=str(HERE),TMP=str(HERE),HF_HUB_OFFLINE='1')
import numpy as np,torch,soundfile as sf
from scipy.signal import resample_poly
from demucs.pretrained import get_model
from demucs.apply import apply_model
torch.set_num_threads(4);torch.manual_seed(34)
model=get_model('04573f0d');assert model.sources[3]=='vocals'
folder=HERE/'vocals';folder.mkdir(exist_ok=True)
for p in sorted((ROOT/'audio').glob('*.ogg'),key=lambda p:(p.stem!='lxbgm14',p.stem)):
    target=folder/(p.stem+'.flac')
    if target.exists():continue
    start=time.time();audio,sr=sf.read(p,dtype='float32',always_2d=True);assert sr==44100 and audio.shape[1]==2
    wave=torch.from_numpy(np.ascontiguousarray(audio.T));avg=wave.mean(0);mean=avg.mean();std=avg.std()
    with torch.inference_mode():
        result=apply_model(model,((wave-mean)/std)[None],device='cuda',shifts=0,split=True,overlap=.25,segment=7.0)[0,3]
    vocal=resample_poly((result.mean(0)*std+mean).cpu().numpy(),160,441).astype('float32')
    tmp=target.with_suffix('.building');sf.write(tmp,vocal,16000,format='FLAC',subtype='PCM_16');os.replace(tmp,target)
    print(p.stem,'seconds',round(len(vocal)/16000,2),'processed',round(time.time()-start,1),flush=True)
