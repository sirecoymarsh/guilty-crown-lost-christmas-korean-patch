"""평평한(폴더 항목 없는) NPA(nss.npa 같은)를 다시 쓴다: 항목 바꾸기 + 새 항목 더하기. 머리(열쇠·압축·암호)는 원본 그대로.
from npa_build import build; build(src, out, replace={'0_boot.nss': b'...'}, add={'kr_scenario.nss': b'...'})
이름 암호는 항목 번호에 걸리므로 표 전체를 새로 쓴다(adapter 의 읽기 식을 거꾸로)."""
import struct, sys, zlib
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
import npa_adapter as A


def build(src, out, replace=None, add=None):
    replace, add = dict(replace or {}), dict(add or {})
    arc = A.NPA(Path(src))
    assert arc.nd == 0 and all(e['type'] == 2 for e in arc.entries), 'flat archives only'
    names = {e['name'] for e in arc.entries}
    assert set(replace) <= names and not (set(add) & names)
    items = []
    for e in arc.entries:
        if e['name'] in replace:
            items.append((e['name_bytes'], replace[e['name']], None))
        else:
            items.append((e['name_bytes'], None, e))          # keep stored bytes as they are
    for n, data in add.items():
        items.append((n.encode('cp932'), data, None))
    prod = arc.k1 * arc.k2
    table = bytearray(); payload = bytearray(); metas = []
    for idx, (nb, data, old) in enumerate(items):
        key = -sum(prod >> s for s in (24, 16, 8, 0)) - sum(idx >> s for s in (24, 16, 8, 0))
        raw_name = bytes((b - 0xfc * j - key) & 255 for j, b in enumerate(nb))
        if old is not None and idx == old['idx']:
            stored, size = arc.raw(old), old['size']
        else:
            if data is None:                                   # moved entry: re-encrypt from plain data
                data = arc.read(old)
            size = len(data)
            raw = bytearray(zlib.compress(data, 9) if arc.comp else data)
            if arc.enc:
                k = (((0x20101118 - sum(nb)) * len(nb) + prod) * size) & 255
                for j in range(min(len(raw), 0x1000 + len(nb))):
                    raw[j] = A.INV[(raw[j] + k + j) & 255]
            stored = bytes(raw)
        off = len(payload); payload.extend(stored)
        table += struct.pack('<I', len(raw_name)) + raw_name + struct.pack('<BIIII', 2, 0, off, len(stored), size)
    head = bytearray(arc.blob[:41])
    struct.pack_into('<ii??III8xI', head, 7, arc.k1, arc.k2, arc.comp, arc.enc, len(items), 0, len(items), len(table))
    blob = bytes(head) + bytes(table) + bytes(payload)
    Path(out).write_bytes(blob)
    chk = A.NPA(Path(out))
    ce = {e['name']: e for e in chk.entries}
    for idx, (nb, data, old) in enumerate(items):
        n = nb.decode('cp932'); e = ce[n]
        if old is not None:
            assert chk.raw(e) == arc.raw(old) if old['name'] != 'function_lc_wam.nss' or True else True
        else:
            assert chk.read(e) == data, n
    return chk


if __name__ == '__main__':
    import tempfile
    src = sys.argv[1]
    out = Path(tempfile.gettempdir()) / 'npa_build_selftest.npa'
    c = build(src, out, add={'kr_selftest.txt': 'テスト 시험'.encode('cp932', 'replace')})
    print('self-test ok', len(c.entries), 'entries', out.stat().st_size, 'bytes')
