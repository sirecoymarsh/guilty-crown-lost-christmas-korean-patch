"""Compile a compensated audio clock into the existing fixed-size saved-script regions."""
import re
# PassageTime reports decoded blocks in 499 ms increments. The native game-output correlation
# measured a median lead of 0.93 s at the first poll observing a new block, with or without seeking.
LEAD_MS=940
BLOCK_MS=499

def fit_block(original, changed, newline):
    missing=original.count(b'\n')-changed.count(b'\n')
    if missing<0:raise ValueError('More lines than reserved in the saved script')
    changed+=newline*missing
    if len(changed)>len(original):raise ValueError(('Saved script has insufficient room',len(original),len(changed)))
    return changed.ljust(len(original))

def modern(source):
    head=b'function KrLyLookup()\n{\n'
    start=source.index(head)+len(head)
    # These evaluations never yield. All later source positions and the module length stay identical.
    end=start
    for _ in range(38):end=source.index(b'\n',end)+1
    block=source[start:end]
    prefix=(
        'if($KLY_RS!=$KLY_TIME||$KLY_RT!=$KLY_TRACK){$KLY_RS=$KLY_TIME;$KLY_RT=$KLY_TRACK;$KLY_T0=MilliTime();}'
        '$KLY_DT=MilliTime()-$KLY_T0;if($KLY_DT<0){$KLY_DT=0;}'
        f'if($KLY_DT>{BLOCK_MS}){{$KLY_DT={BLOCK_MS};}}'
        f'$KLT=$KLY_TIME+$KLY_DT-{LEAD_MS};$KLY_TIME=$KLT;'
    ).encode('ascii')
    changed=prefix+block.replace(b'$KLY_TIME',b'$KLT')
    return source[:start]+fit_block(block,changed,b'\n')+source[end:]

def legacy(block):
    # Store the Sound Mode row just once, freeing space for the native clock in the original byte range.
    def music_row(m):
        return b'$AWk=='+m[1]
    smaller,n=re.subn(rb'\(\$AWh=="@kubgm"&&\$AWrow==(\d+)\)',music_row,block)
    assert n==10
    smaller=b'$AWk=0;if($AWh=="@kubgm"){$AWk=$AWrow;}'+smaller
    a=b'else{$AWstill=0;}'
    b=b'$AWprev=$AWms;$AWcue=0;'
    assert smaller.count(a)==smaller.count(b)==1
    smaller=smaller.replace(a,b'else{$AWstill=0;$AWmark=MilliTime();}')
    step=(f'$AWprev=$AWms;$AWde=MilliTime()-$AWmark;if($AWde<0){{$AWde=0;}}'
          f'if($AWde>{BLOCK_MS}){{$AWde={BLOCK_MS};}}$AWms+=$AWde-{LEAD_MS};$AWcue=0;')
    return fit_block(block,smaller.replace(b,step.encode('ascii')),b'\r\n')
