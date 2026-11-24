"""Play across all ten final lyric releases and meter the isolated game with the same Windows clock as its trace."""
import csv,ctypes,json,os,shutil,subprocess,sys,threading,time
from pathlib import Path
import runtime_test as rt
HERE,AW=rt.HERE,rt.AW
def monitor_pid(pid,out):
    h=rt.run_test.H
    deadline=time.monotonic()+12
    sessions=[]
    while not sessions and time.monotonic()<deadline:
        sessions=h.sessions_of(pid)
        if not sessions:time.sleep(.12)
    if not sessions:raise RuntimeError('No isolated game audio session')
    clock=ctypes.windll.kernel32.GetTickCount64
    clock.restype=ctypes.c_ulonglong
    with out.open('x',newline='') as f:
        writer=csv.writer(f);writer.writerow(['uptime_ms','game_peak'])
        while time.monotonic()<deadline+125 and h.pids_of(AW/'game',rt.run_test.EXE):
            for _ in range(35):
                writer.writerow([clock()&0xffffffff,max(h.peak(m) for _,m in sessions)])
                time.sleep(.009)
    for v,m in sessions:h.release(v);h.release(m)
def sweep(name, flavor='latest'):
    rows=json.loads((HERE/'accepted.json').read_text(encoding='utf8'))['cues']
    tracks=list(dict.fromkeys(c['track'] for c in rows));script=[]
    inputs={}
    for j,tr in enumerate(tracks,1):
        last=[c for c in rows if c['track']==tr][-1];seek=last['end']-4200
        inputs[str(j)]={'track':tr,'cue':last['id'],'end':last['end'],'seek':seek}
        script.extend([f'CreateBGM("kubgm","{tr}");SoundPlay("@kubgm",0,1000,true);SetStream("@kubgm",{seek});', 'Wait(8600);SetVolumeEX("@kubgm",0,0,null);Request("@kubgm",Stop);Request("@kubgm",UnLock);Delete("@kubgm");Wait(200);'])
    if name == 'natural-clock':
        inputs={'5':{'track':'lxbgm14','cue':182,'end':37600,'seek':0}}
        script=['CreateBGM("lx014","lxbgm14");SoundPlay("@lx014",0,1000,true);Wait(42400);']
    script.append('CreateTexture("done",1,0,0,"nss/kr_cmd_traceallendsdone.png");Wait(120000);')
    boot=('#include "nss/function.nss"\nchapter main\n{\n#N2Start=true;#SYSTEM_window_full=false;\n'+'\n'.join(script)+'\n}\n').replace('\n','\r\n').encode('ascii')
    arc=rt.NPA(HERE/flavor/'nss.npa');ent=next(e for e in arc.entries if e['name']=='kr_lyrics.nss')
    src=arc.read(ent);anchor=b'KrLyShow();Wait(100);';assert src.count(anchor)==1
    marker=b'KrLyShow();$es=$KLY_TIME;if($es!=$esprev){$esprev=$es;$ep=String("nss/kr_cmd_tracefin_T%d_C%d_M%d.png",$KLY_TRACK,$KLY_SHOWN,$es);CreateTexture("ep",1,0,0,$ep);Delete("ep");}Wait(100);'
    (AW/'variants/timing-all-ends.npa').write_bytes(arc.pack({'0_boot.nss':boot,'kr_lyrics.nss':src.replace(anchor,marker)}))
    game=AW/'game'
    shutil.copyfile(HERE/'build'/('merged' if flavor=='latest' else 'deployed')/'payload/n2hd_runtime.dll',game/'n2hd_runtime.dll')
    shutil.copytree(rt.BGM/'payload/lyrics-resume',game/'lyrics-resume',dirs_exist_ok=True)
    shutil.copytree(HERE/'tables',game/'lyrics-resume',dirs_exist_ok=True)
    original=rt.run_test.run_game
    def run(a,r,profile):
        (r/'windows.json').write_text(json.dumps(inputs,indent=2),encoding='utf8')
        def collect():
            deadline=time.monotonic()+17
            pids=[]
            while time.monotonic()<deadline and not pids:
                pids=rt.run_test.H.pids_of(game,rt.run_test.EXE)
                if not pids:time.sleep(.08)
            if not pids:return
            with (r/'meter-log.txt').open('w') as output:
                subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'capture',str(pids[0]),str(r/'meter.csv')],stdout=output,stderr=subprocess.STDOUT)
        worker=threading.Thread(target=collect);worker.start()
        try:original(a,r,profile)
        finally:worker.join(5)
    rt.run_test.run_game=run
    sys.argv=[sys.argv[0],name,'--nss','timing-all-ends.npa','--art-off','--no-jump','--seconds','125','--stop-trace','traceallendsdone','--stop-delay','1','--shot-ms','0']
    rt.run_test.main()
if __name__=='__main__':
    if sys.argv[1]=='capture':monitor_pid(int(sys.argv[2]),Path(sys.argv[3]))
    else:sweep(sys.argv[1])
