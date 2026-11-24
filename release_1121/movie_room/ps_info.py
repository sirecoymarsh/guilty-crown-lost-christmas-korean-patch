"""MPEG 프로그램 스트림(.ngs) 머리 정보 비교: 묶음 mux_rate, 시스템 머리 rate_bound·P-STD 버퍼, 영상 PES 길이, 묶음 간격,
그리고 MPEG-2 sequence_header 의 bit_rate_value · vbv_buffer_size_value(+ sequence_extension 의 위쪽 비트).
python -I -X utf8 ps_info.py 파일...
"""
import sys


def seq_fields(b):
    i = b.find(b'\x00\x00\x01\xb3')
    s = b[i + 4:i + 12]
    br = (s[4] << 10) | (s[5] << 2) | (s[6] >> 6)
    vbv = ((s[6] & 0x1f) << 5) | (s[7] >> 3)
    j = b.find(b'\x00\x00\x01\xb5', i)
    e = b[j + 4:j + 10]
    ext_id = e[0] >> 4
    br_ext = ((e[2] & 0x1f) << 7) | (e[3] >> 1) if ext_id == 1 else None
    vbv_ext = e[4] if ext_id == 1 else None
    return {'bit_rate_value': br, 'vbv_buffer_size_value': vbv, 'ext_id': ext_id, 'bit_rate_ext': br_ext, 'vbv_ext': vbv_ext}


def ps_info(p):
    b = open(p, 'rb').read(600000)
    out = {}
    i = b.find(b'\x00\x00\x01\xba')
    h = b[i + 4:i + 14]
    out['mpeg2_pack'] = (h[0] >> 6) == 1
    out['mux_rate'] = (h[6] << 14) | (h[7] << 6) | (h[8] >> 2)
    j = b.find(b'\x00\x00\x01\xbb')
    if j >= 0:
        L = int.from_bytes(b[j + 4:j + 6], 'big'); s = b[j + 6:j + 6 + L]
        out['rate_bound'] = ((s[0] & 0x7f) << 15) | (s[1] << 7) | (s[2] >> 1)
        k = 6; st = []
        while k + 3 <= len(s):
            st.append((hex(s[k]), (((s[k + 1] & 0x1f) << 8) | s[k + 2]) * (1024 if (s[k + 1] >> 5) & 1 else 128))); k += 3
        out['pstd'] = st
    sizes = []; k = 0
    while len(sizes) < 4:
        k = b.find(b'\x00\x00\x01\xe0', k)
        if k < 0: break
        sizes.append(int.from_bytes(b[k + 4:k + 6], 'big')); k += 4
    out['video_pes_len'] = sizes
    p1 = b.find(b'\x00\x00\x01\xba'); p2 = b.find(b'\x00\x00\x01\xba', p1 + 4); p3 = b.find(b'\x00\x00\x01\xba', p2 + 4)
    out['pack_gaps'] = (p2 - p1, p3 - p2)
    out['seq'] = seq_fields(b)
    return out


for p in sys.argv[1:]:
    print(p, ps_info(p))
