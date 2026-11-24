"""DLL 들에 기능 표지 문자열이 들어 있는지 본다(읽기만).  python -X utf8 dll_markers.py <dll> [...]"""
import hashlib, sys
MARKS = ['KeyBar', '#KR_JP', 'hires_ui', 'N2HD_TEST_CURSOR_FILE', 'kr_cmd_', 'Resizable', 'NotoSansCJKjp', 'kr_keybar', 'FlipModel', 'IdleHalf',
         'N2HD_TEST_LOCKFIX_OFF', 'locks.log', 'keys.log', '$TypeBeginIn', 'KR_REPLAY', 'jtext', 'lyrics', 'subtitle', 'awaken', 'karaoke', 'KR_LY', 'KLY']
for p in sys.argv[1:]:
    b = open(p, 'rb').read()
    print(hashlib.sha256(b).hexdigest()[:8], len(b), p)
    row = []
    for m in MARKS:
        a = b.count(m.encode('ascii')); w = b.count(m.encode('utf-16le'))
        row.append(f'{m}={a}/{w}')
    print('   ', '  '.join(row))
