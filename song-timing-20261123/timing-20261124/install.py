"""Install the tested subtitle archive and native reader together into the existing play copy."""
import hashlib,json,os,shutil,sys,uuid
from datetime import datetime
from pathlib import Path
from package import AW,BGM,HERE,LIVE,SHARED,archive
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf8'))
def record(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def prepare():
    checks=read(HERE/'archive-check.json')
    for name,base in [('play',LIVE/'nss.npa'),('latest',SHARED/'staging/nss_play.npa')]:
        current=digest(base);target=HERE/name/'nss.npa'
        if current not in (checks[name]['source_hash'],checks[name]['target_hash']):
            checks[name],_,_=archive(base,HERE/name)
            if digest(base)!=checks[name]['source_hash']:raise RuntimeError('Archive changed during preparation')
        assert digest(target)==checks[name]['target_hash']
        folder=HERE/name/'lyrics-resume';folder.mkdir(exist_ok=True)
        for origin in [BGM/'payload/lyrics-resume',HERE/'tables']:
            for f in origin.glob('*.n2l'):shutil.copyfile(f,folder/f.name)
        assert len(list(folder.glob('*.n2l')))==8
        mode='merged' if name=='latest' else 'deployed'
        shutil.copyfile(HERE/'build'/mode/'payload/n2hd_runtime.dll',HERE/name/'n2hd_runtime.dll')
    record(HERE/'archive-check.json',checks)
    if digest(SHARED/'engine/payload/n2hd_runtime.dll')!=read(HERE/'build/merged/base.json')['shared_runtime_sha256']:
        raise RuntimeError('Claude engine has changed since the tested merge')
    return checks
def copy_checked(src,dest,expected,backup):
    tmp=dest.with_name('.lyrics-'+uuid.uuid4().hex+'.tmp')
    try:
        shutil.copyfile(src,tmp)
        assert digest(src)==digest(tmp)
        present=digest(dest) if dest.exists() else None
        if present!=expected:raise RuntimeError('Destination changed during installation: '+str(dest))
        try:os.replace(tmp,dest)
        except PermissionError as exc:
            if exc.winerror not in (5,32) or dest.name not in ('nss.npa','n2hd_runtime.dll') or not expected or digest(dest)!=expected:raise
            # Windows may allow an open file to move while denying replacement. Keep the loaded image alive.
            held=backup/('open-'+uuid.uuid4().hex+dest.suffix)
            os.rename(dest,held)
            try:os.rename(tmp,dest)
            except BaseException:
                if not dest.exists():os.rename(held,dest)
                raise
    finally:tmp.unlink(missing_ok=True)
def install():
    deploy=HERE/'deployment';deploy.mkdir(exist_ok=True)
    if (deploy/'installed.json').is_file():
        done=read(deploy/'installed.json')
        if all((LIVE/k).is_file() and digest(LIVE/k)==v for k,v in done['installed'].items()):
            print('Verified already-installed playback copy');return
        raise RuntimeError('Play copy changed after this revision was installed')
    metrics=read(HERE/'runtime-verification.json')
    assert metrics['all_endings_passed']==10 and metrics['lookup_cases_passed']==20 and metrics['legacy_display_samples']>8
    checks=prepare();previous_install=read(BGM/'deployment/installed.json')['installed']
    target=HERE/'play'
    if digest(LIVE/'n2hd_runtime.dll')!=previous_install['n2hd_runtime.dll']:raise RuntimeError('Live runtime was independently replaced')
    for k,v in previous_install.items():
        if k.startswith('lyrics-resume/') and (digest(LIVE/k)!=v or digest(target/k)!=v):raise RuntimeError('Existing BGM recovery map changed: '+k)
    plan={f'lyrics-resume/{f.name}':f for f in sorted((target/'lyrics-resume').glob('*.n2l'))}
    plan['nss.npa']=target/'nss.npa';plan['n2hd_runtime.dll']=target/'n2hd_runtime.dll'
    old={k:digest(LIVE/k) if (LIVE/k).exists() else None for k in plan}
    assert old['nss.npa']==checks['play']['source_hash']
    for k in plan:
        if k.startswith('lyrics-resume/timing-') and old[k] not in (None,digest(plan[k])):raise RuntimeError('Unknown pre-existing subtitle table '+k)
    backups=deploy/'rollback';backups.mkdir(exist_ok=True)
    for k,v in old.items():
        if v is None or v==digest(plan[k]):continue
        f=backups/k;f.parent.mkdir(parents=True,exist_ok=True)
        if not f.exists():shutil.copyfile(LIVE/k,f)
        assert digest(f)==v
    done=[]
    try:
        for k,f in plan.items():
            if old[k]!=digest(f):copy_checked(f,LIVE/k,old[k],deploy);done.append(k)
        installed={k:digest(LIVE/k) for k in plan}
        assert all(installed[k]==digest(f) for k,f in plan.items())
    except BaseException:
        for k in reversed(done):
            if digest(LIVE/k)!=digest(plan[k]):raise RuntimeError('Concurrent replacement while rolling back '+k)
            if old[k] is None:(LIVE/k).unlink()
            else:copy_checked(backups/k,LIVE/k,digest(plan[k]),deploy)
        raise
    record(deploy/'installed.json',{'at':datetime.now().astimezone().isoformat(),'game':str(LIVE),'previous':old,'installed':installed,'changed':done,'native_user_saves_written':False,'latest_shared_archive':checks['latest'],'latest_engine_base':read(HERE/'build/merged/base.json')['shared_runtime_sha256']})
    print('Installed and verified',len(done),'changed files:',installed['nss.npa'],installed['n2hd_runtime.dll'])
if __name__=='__main__':
    if sys.argv[1:] == ['prepare']:prepare()
    else:install()
