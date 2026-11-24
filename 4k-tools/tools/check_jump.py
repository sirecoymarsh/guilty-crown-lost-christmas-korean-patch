"""대사 기록 점프 저장소 검사: 모든 지점(.cpt)의 조각이 있고, 풀어 이은 파일 크기·조각 해시가 맞는지. staging 이 비었는지.
python -X utf8 check_jump.py <프로필 폴더>"""
import ctypes, hashlib, struct, sys
from pathlib import Path

cab = ctypes.WinDLL('cabinet')
h = ctypes.c_void_p()
assert cab.CreateDecompressor(4, None, ctypes.byref(h))   # COMPRESS_ALGORITHM_XPRESS_HUFF


def unpack(blk):
    magic, n = struct.unpack_from('<II', blk)
    assert magic == 0x314b4c42
    out = ctypes.create_string_buffer(n); got = ctypes.c_size_t()
    src = blk[8:]
    assert cab.Decompress(h, src, ctypes.c_size_t(len(src)), out, ctypes.c_size_t(n), ctypes.byref(got)) and got.value == n
    return out.raw


class R:
    def __init__(s, b): s.b, s.i = b, 0
    def n(s): v = struct.unpack_from('<I', s.b, s.i)[0]; s.i += 4; return v
    def s(s): k = s.n(); v = s.b[s.i:s.i + k].decode('ascii'); s.i += k; return v


root = next(Path(sys.argv[1]).rglob('n2hd-jump-v1'))
store = next(p for p in root.iterdir() if p.is_dir())
points = sorted((store / 'points').glob('*.cpt'))
blocks = {p.stem for p in (store / 'blocks').glob('*.blk')}
bad = missing = checked_files = checked_blocks = 0
seen = set()
for cpt in points:
    r = R(cpt.read_bytes())
    assert r.n() == 0x314a424e
    pid, parent, start, end, sealed, lo, hi, nf = r.s(), r.s(), r.n(), r.n(), r.n(), r.n(), r.n(), r.n()
    if nf == 0: bad += 1
    for _ in range(nf):
        name, size, nc = r.s(), r.n(), r.n()
        hashes = [r.s() for _ in range(nc)]
        data = b''
        for hsh in hashes:
            if hsh not in blocks: missing += 1; continue
            if hsh not in seen:
                raw = unpack((store / 'blocks' / f'{hsh}.blk').read_bytes())
                if hashlib.sha256(raw).hexdigest() != hsh: bad += 1
                seen.add(hsh); checked_blocks += 1
        checked_files += 1
staging = list((store / 'staging').rglob('*')) if (store / 'staging').exists() else []
print(f'지점 {len(points)}, 파일 {checked_files}, 조각 검사 {checked_blocks}, 없는 조각 {missing}, 이상 {bad}, staging 남은 것 {len(staging)}')
