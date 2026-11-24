from pathlib import Path
import sys,os,json,shutil,re,struct,hashlib
HERE=Path(r'P:\AI\Codex\projects\gclx-song-20261123\timing-20261124');ROOT=HERE.parent
AW=ROOT/'awakening';BGM=AW/'bgm-output'
os.environ.update(GCLX_GAME=str(AW/'game'),GCLX_RUNS=str(HERE/'runs'),GCLX_NSS_DIR=str(AW/'variants'),TEMP=str(HERE),TMP=str(HERE))
sys.path[:0]=[str(BGM),str(AW),str(ROOT/'tools')]
from npa_adapter import NPA,KEY,INV
from save_lyrics import decode_program,MODULE
from make_tables import transitions,patched
import run_test
from legacy_audio import decorate
from clock_patch import LEAD_MS
def prepare():
    game=AW/'game';shutil.copyfile(HERE/'build/deployed/payload/n2hd_runtime.dll',game/'n2hd_runtime.dll')
    shutil.copytree(BGM/'payload/lyrics-resume',game/'lyrics-resume',dirs_exist_ok=True);shutil.copytree(HERE/'tables',game/'lyrics-resume',dirs_exist_ok=True)
    a=NPA(HERE/'play/nss.npa');e={x['name']:x for x in a.entries}
    script=a.read(e['kr_lyrics.nss']);token=b'KrLyShow();Wait(100);';assert script.count(token)==1
    marker=b'KrLyShow();$tmw+=1;if($tmw>=3){$tmw=0;$tmf=String("nss/kr_cmd_traceclock_C%d_M%d_Y%d.png",$KLY_CUE,$KLY_TIME,$KLY_Y);CreateTexture("tmwlog",1,0,0,$tmf);Delete("tmwlog");}Wait(100);'
    script=script.replace(token,marker)
    checks=[];ref=[];rows=json.loads((HERE/'reviewed.json').read_text(encoding='utf8'))
    for t,track in enumerate(dict.fromkeys(r['track'] for r in rows),1):
        rr=[r for r in rows if r['track']==track]
        r=max(rr,key=lambda z:z['new'][1]-z['old'][1]);mid=round(1000*(r['old'][1]+r['new'][1])*.5);end=round(r['new'][1]*1000)
        for ms in (mid,end):
            expect=next((z['id'] for z in rr if round(z['new'][0]*1000)<=ms<round(z['new'][1]*1000)),0)
            ref.append([t,ms,expect]);checks.append(f'$KLY_CUE=0;$KLY_TRACK={t};$KLY_RS=-1;$KLY_TIME={ms+LEAD_MS};KrLyLookup();$tf=String("nss/kr_cmd_tracetbl_{t}_{ms}_%d.png",$KLY_CUE);CreateTexture("tm",1,0,0,$tf);Delete("tm");')
    (HERE/'lookup-expected.json').write_text(json.dumps(ref),encoding='ascii')
    boot='''#include "nss/function.nss"
chapter main
{
 #N2Start=true;#SYSTEM_window_full=false;
 CreateColor("bg",1,0,0,1024,576,0x393344);
 CHECKS
 $KLY_TRACK=0;
 CreateBGM("kubgm","lxbgm14");SoundPlay("@kubgm",0,1000,true);SetStream("@kubgm",34000);
 Wait(7200);SetVolumeEX("@kubgm",0,0,null);Request("@kubgm",Stop);
 CreateBGM("lx014","lxbgm14");SoundPlay("@lx014",0,600,true);SetStream("@lx014",44700);
 Wait(7000);SetVolumeEX("@lx014",0,0,null);Wait(120000);
}
'''.replace('CHECKS','\n'.join(checks)).replace('\n','\r\n').encode('ascii')
    (AW/'variants/timing-probe.npa').write_bytes(a.pack({'0_boot.nss':boot,'kr_lyrics.nss':script}))
def run_modern():
    sys.argv=[sys.argv[0],os.environ.get('TIMING_MODERN_RUN','sound-and-story'),'--nss','timing-probe.npa','--art-off','--no-jump','--seconds','38','--shot-ms','0']
    run_test.main()
def run_old():
    game=AW/'game'
    s,k=decode_program((AW/'runs/regular-old-slot/profile/Nitroplus/GUILTY CROWN LOST XMAS/1.00/0011/script.npf').read_bytes());m=MODULE.search(s)
    orig=s[m.end():m.end()+struct.unpack('<I',m[1])[0]];enc=bytes(INV[(i+k)&255] for i in range(256))
    diag=transitions(orig.translate(enc),decorate(orig,True).translate(enc),s[m.start():m.end()].translate(enc))
    orig_run=run_test.run_game;data=game/'lyrics-resume/data.n2l';prod=data.read_bytes();data.write_bytes(diag)
    def seed(a,r,prof):
        root=prof/'Nitroplus/GUILTY CROWN LOST XMAS/1.00';prior=AW/'runs/installed-hill/profile/Nitroplus/GUILTY CROWN LOST XMAS/1.00'
        for n in ('0011','images','common'):
            if (prior/n).exists():shutil.copytree(prior/n,root/n,dirs_exist_ok=True)
        f=root/'0011/frames.npf';raw=f.read_bytes();arr=raw[16:];key=(KEY[arr[0]]-78)&255;plain=bytearray(arr.translate(bytes((i-key)&255 for i in KEY)))
        idx=plain.index(b'CreateSound("lx014",BGM,"sound/bgm/lxbgm14");');q=plain.index(b');',idx)+2+4
        for _ in range(4):q=plain.index(b'\0',q)+4
        assert struct.unpack_from('<II',plain,q+141)==(300,44100)
        struct.pack_into('<I',plain,q+153,round(32.5*44100)*4)
        f.write_bytes(raw[:16]+bytes(plain).translate(bytes(INV[(i+key)&255] for i in range(256))))
        return orig_run(a,r,prof)
    run_test.run_game=seed;sys.argv=[sys.argv[0],os.environ.get('TIMING_LEGACY_RUN','legacy-story'),'--nss','bgm-current-load.npa','--art-off','--no-jump','--seconds','37','--shot-ms','0']
    try:run_test.main()
    finally:data.write_bytes(prod)
if __name__=='__main__':
    if sys.argv[1]=='modern':prepare();run_modern()
    else:run_old()
