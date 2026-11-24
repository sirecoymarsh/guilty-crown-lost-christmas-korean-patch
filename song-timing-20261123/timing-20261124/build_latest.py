"""Rebuild the exact engine variants without replacing the player's independently installed optional features."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'awakening'/'bgm-output'))
import build_runtime as builder
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    shared=builder.SHARED
    tested=builder.WORK/'runtime'/'src'/'lyric_save_view.inc'
    # Overlay the player's compatibility extension only on the known upstream implementation.
    shared_inc=shared/'src'/'lyric_save_view.inc'
    known_reader={digest(tested),digest(builder.WORK/'bgm-output/build/merged/src/lyric_save_view.inc')}
    if digest(shared_inc) not in known_reader:
        raise RuntimeError('The upstream save reader has changed; merge its behavior before building.')
    dll=shared/'payload'/'n2hd_runtime.dll'
    if (shared/'src/bgm_recovery.inc').exists() and digest(shared/'src/bgm_recovery.inc')!=digest(builder.WORK/'bgm_recovery.inc'):
        raise RuntimeError('Upstream gain recovery changed')
    snapshot={f.name:digest(f) for f in (shared/'src').iterdir() if f.suffix in ('.cpp','.inc','.h')}
    base=digest(dll)
    builder.HERE=HERE
    builder.NAMES['merged']=(shared,base)
    builder.build('merged')
    assert digest(dll)==base and all(digest(shared/'src'/n)==s for n,s in snapshot.items())
    for n,s in snapshot.items():
        if n not in ('bgm_recovery.inc','lyric_save_view.inc'):assert digest(HERE/'build/merged/src'/n)==s,n
    result={'shared_runtime_sha256':base,'input_sources':snapshot,'output_sha256':digest(HERE/'build/merged/payload/n2hd_runtime.dll')}
    (HERE/'build/merged/base.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
if __name__=='__main__':main()
