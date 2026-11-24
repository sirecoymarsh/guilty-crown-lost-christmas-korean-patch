"""2장 영상(mv_lx0201.ngs) 멈춤 고치기(11-23): 코덱스 10-26 판·11-21 판 모두 게임 엔진에서 첫 장면에 멈춘다(원작 영문판 파일은 같은 시험에서 재생됨).
원작과 다른 점: ① MPEG-2 영상을 MPEG-1 묶음(system stream)에 담음 — 원작은 MPEG-2 묶음(2048바이트 pack)
                ② sequence_header 의 vbv_buffer_size_value = 3 — 원작 112, bit_rate_value 262143 — 원작 46250
다시 인코딩하지 않는다: ① 원래 묶음 안의 모든 sequence_header 두 칸을 원작 값으로 고치고(그래야 ffmpeg 묶개가 P-STD 버퍼·mux_rate 를
원작처럼 잡는다) ② ffmpeg 로 MPEG-2 묶음(vob, 2048)으로 옮겨 담고(-c copy) ③ 옮긴 뒤 다시 한 번 확인·고침.
python -I -X utf8 fix_ngs.py <입력.ngs> <출력.ngs>
"""
import subprocess, sys, hashlib
from pathlib import Path
FF = r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\vendor\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe'
VBV, BR = 112, 46250


def patch(b):
    """모든 sequence_header 의 bit_rate_value·vbv_buffer_size_value. 머리 8바이트가 묶음 경계에 걸린 것은 센다."""
    n = bad = 0; i = 0
    while True:
        i = b.find(b'\x00\x00\x01\xb3', i)
        if i < 0:
            return n, bad
        s = i + 4
        if b'\x00\x00\x01' in bytes(b[s:s + 8]):
            bad += 1; i += 4; continue
        b[s + 4] = (BR >> 10) & 0xff
        b[s + 5] = (BR >> 2) & 0xff
        b[s + 6] = ((BR & 0x3) << 6) | (b[s + 6] & 0x20) | (VBV >> 5)
        b[s + 7] = ((VBV & 0x1f) << 3) | (b[s + 7] & 0x07)
        n += 1; i += 4


src, dst = Path(sys.argv[1]), Path(sys.argv[2])
pre = dst.with_suffix('.pre.ngs'); mux = dst.with_suffix('.mux.ngs')
b = bytearray(src.read_bytes()); n1, bad1 = patch(b); pre.write_bytes(bytes(b))
subprocess.run([FF, '-hide_banner', '-loglevel', 'error', '-y', '-f', 'mpeg', '-i', str(pre), '-map', '0', '-c', 'copy',
                '-f', 'vob', '-packetsize', '2048', str(mux)], check=True)
b = bytearray(mux.read_bytes()); n2, bad2 = patch(b)
dst.write_bytes(bytes(b)); pre.unlink(); mux.unlink()
print('patched before mux', n1, 'split', bad1, '| after mux', n2, 'split', bad2, '|', dst.name, len(b), hashlib.sha256(bytes(b)).hexdigest()[:8])
