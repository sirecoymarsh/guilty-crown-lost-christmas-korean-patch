"""놀이 사본 P:\\AI\\gclx-codexrun\\game 에 1.0 출고 파일을 넣는다(사용자 11-21 「다 고쳐」 — 새 번역을 게임에 넣기).
게임이 켜져 있으면 멈춘다. 바뀌는 파일은 먼저 backup_before_1121\\ 에 보관하고, 하드 링크일 수 있는 자리는 링크를 끊고 쓴다.
python -I -X utf8 install_play.py
"""
import hashlib, shutil, subprocess, json, time
from pathlib import Path
W = Path(__file__).resolve().parent
GAME = Path(r'P:\AI\gclx-codexrun\game')
import sys
BK = W / 'backup_before_1124m'   # 11-24 열셋째(회상 재생 전 이야기 상태 맞추기 KsRouteState, nss.fix.npa bbe4e90a) 설치 전: nss.fix 0f88f3af
_BK_1124l = W / 'backup_before_1124l'   # 11-24 열두째(회상 상세 「이 장면의 연출」 단추 nss.fix.npa) 설치 전: nss.fix f65ca998
_BK_1124k = W / 'backup_before_1124k'   # 11-24 열한째(타이틀 위아래 띠 없앰 cg.fix.npa fb1f6fb2) 설치 전: cg.fix 12e7dd02
_BK_1124j = W / 'backup_before_1124j'   # 11-24 열째(영상 감상 다섯 칸 nss.fix.npa) 설치 전: nss 333a6a67·DLL f95a48b5 그대로
_BK_1124i = W / 'backup_before_1124i'   # 11-24 아홉째(병기 한 문장 묶기·phase 표지·곡 바꾸기 멈춤·코덱스 자막 싱크 가사 모듈) 설치 전: nss 13dd4641(코덱스)·DLL f568a117 그대로
_BK_1124h = W / 'backup_before_1124h'   # 11-24 여덟째(사운드 화면 멈춤 고침, nss 만) 설치 전: nss 302254aa·DLL 54196c77(코덱스 시나리오 노래 자막 판)
_BK_1124g = W / 'backup_before_1124g'   # 11-24 일곱째(J/K 바로 바꾸기·곡 제목 풀이·옛 세이브 키 목록·병기 5곳·대사 고침) 설치 전: nss 4ad1e287·DLL bc313603
_BK_1124f = W / 'backup_before_1124f'   # 11-24 여섯째(회상 꺼짐 고침·곡 줄 막대·영상 썸네일·읽은 글 색) 설치 전: nss d85c85c6·DLL bc313603
_BK_1124e = W / 'backup_before_1124e'   # 11-24 다섯째(로고·회상 휠·크레딧·J/K 교차) 설치 전: nss e3e9c5f6·DLL 5d25842f
_BK_1124d = W / 'backup_before_1124d'   # 11-24 넷째(아이콘) 설치 전: DLL af71ace9
_BK_1124c = W / 'backup_before_1124c'   # 11-24 셋째 설치 전(nss cb9cef1d·DLL 503f77b7)
_BK_1124b = W / 'backup_before_1124b'   # 11-24 둘째 설치 전(nss 1d7e6ce8·DLL 503f77b7)
_BK_1124 = W / 'backup_before_1124'   # 11-24 노래 가사(코덱스 nss 1d7e6ce8)·테두리 커서 DLL: 그 전 판(nss 53de61c8·DLL ae5246e8)
_BK_1123 = W / 'backup_before_1123'   # 11-23 영상 감상·2장 영상 MPEG-1: 그 전 판(nss acbad13c·DLL f943934a·ngs bafb9e91)을 따로 보관
FILES = {
    'nss.npa': W / 'staging/nss_play.npa',   # 11-24 둘째: nss_lyrics + sound_seek/patch_seek.py(사운드 진행 막대·가사 위·노랑·상자 없음·회상 요약 자리·「재생」)   # 11-24: nss_final(53de61c8) + 코덱스 노래 가사(gclx-song-20261123, 6개 고침·367개 더함)
    'n2hd_runtime.dll': W / 'engine/payload/n2hd_runtime.dll',
    'version.dll': W / 'proxy/version.dll',
    'fonts/NotoSansCJKjp-Medium.otf': W / 'sound_seek/NotoSansCJKjp-Medium.otf',   # 11-24 J: 본문 일본어 글꼴(OFL)
    'fonts/OFL-notosanscjkjp.txt': W / 'sound_seek/OFL-notosanscjkjp.txt',
    'dx/mv_lx0201.ngs': W / 'movie_room/fixed/mv_lx0201.ngs',   # 11-23: MPEG-2 → MPEG-1(엔진이 MPEG-2 를 첫 장면에서 멈춤)
    'dx4k/mv_lx0201.mp4': W / 'movie/out/mv_lx0201.mp4',
    # 11-24 단계 표지 「단계」 → 원작 영어 「phase」: 그림 하나만 든 덧씌우기 묶음(이름순 첫 묶음이 이김, phase/make_cgfix.py)
    'cg.fix.npa': W / 'phase/cg.fix.npa',
    # 11-24 오후 영상 감상에 1장 전투 영상 칸(5칸): 영상 감상 항목 8개만 든 덧씌우기 묶음(movie_room/make_nssfix.py).
    # nss.npa 를 그대로 두려고 — 코덱스 세이브 호환이 nss.npa 해시를 확인한다(아래 지킴 참고).
    'nss.fix.npa': W / 'movie_room/nss.fix.npa',
}
# 11-24 engine\payload 는 이제 공용 소스(잠금 고침 v3.1) + 코덱스 lyric_save_view·bgm_recovery 를 합친 판(a7c303d3, 다른 세션 「사운드 모드 성능」).
# 코덱스가 깐 lyrics-resume\*.n2l 다섯 파일은 이 설치가 건드리지 않는다(그대로 두어야 함).
# 11-24: 문장 끝 아이콘 4배(코덱스 그림, icons_hd/pack_ui.py) — 본 패치 hires_ui\ (DLL 이 hires\ 다음으로 읽는 둘째 목록)
for _p in sorted((W / 'icons_hd/hires_ui').iterdir()):
    FILES['hires_ui/' + _p.name] = _p
# 11-24 07:04 코덱스가 놀이 사본에 시나리오 노래 자막 DLL(54196c77 = engine\src ac07b4a7 + lyric_save_view.inc)과
# lyrics-resume\*.n2l 을 넣었다. engine\payload 는 아직 그 소스를 품지 않으므로 --nss-only 로 대본만 넣는다(DLL 을 덮으면 코덱스 기능이 빠짐).
if '--nss-only' in sys.argv:
    FILES = {'nss.npa': FILES['nss.npa']}
# 11-24 08:54 코덱스가 보컬 자막 싱크 DLL(f568a117)을 놀이 사본에 넣음 — 합친 DLL 이 나올 때까지 DLL 은 건드리지 않는다
if '--no-dll' in sys.argv:
    FILES.pop('n2hd_runtime.dll')
# 11-24 오후: 덧씌우기 묶음만(--fix-only). 새로 생기는 파일뿐이면 게임이 켜져 있어도 넣는다(켜진 게임은 다음 실행부터 읽음).
FIX_ONLY = '--fix-only' in sys.argv
if FIX_ONLY:
    FILES = {'nss.fix.npa': FILES['nss.fix.npa']}
# 11-24 오후: 한 파일만(--only=cg.fix.npa 등, 타이틀 위아래 띠 없애기)
_only = [a.split('=', 1)[1] for a in sys.argv if a.startswith('--only=')]
if _only:
    FILES = {k: FILES[k] for k in _only}
# 11-24 지킴: 코덱스 세이브 호환(lyrics-resume\story-resume.n2r + krresume.npa)은 설치된 nss.npa 의 SHA-256 에 묶여 있다
# (story_resume.inc sameFile(..\nss.npa)). 다른 nss.npa 를 깔면 옛 세이브 이어하기가 조용히 꺼진다 → 코덱스와 맞춘 뒤
# --nss-codex-ok 로만. 그때 nss.fix.npa 는 지울 것(새 nss.npa 에 같은 내용이 들어 있고, 남으면 뒤의 고침을 가린다).
if 'nss.npa' in FILES and (GAME / 'lyrics-resume/story-resume.n2r').exists() and '--nss-codex-ok' not in sys.argv:
    if hashlib.sha256((GAME / 'nss.npa').read_bytes()).hexdigest() != hashlib.sha256(FILES['nss.npa'].read_bytes()).hexdigest():
        raise SystemExit('nss.npa 가 바뀜 — 코덱스 세이브 호환 자료를 다시 만들어야 함. 맞춘 뒤 --nss-codex-ok (또는 --no-nss)')
if '--no-nss' in sys.argv:
    FILES.pop('nss.npa', None)


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            h.update(b)
    return h.hexdigest()

# 11-24: 놀이 사본에서 띄운 것만 본다(숨긴 시험 사본 P:\AI\gclx-reltest 의 게임은 상관없음)
r = subprocess.run(['powershell', '-NoProfile', '-Command',
                    "Get-Process | Where-Object { $_.Path -like '" + str(GAME) + "*' } | ForEach-Object { $_.Path }"],
                   capture_output=True, text=True, encoding='cp949', errors='replace')
if r.stdout.strip() and not (FIX_ONLY and not any((GAME / rel).exists() for rel in FILES)):
    raise SystemExit('게임이 켜져 있음 — 설치하지 않음: ' + r.stdout.strip())
rep = {'time': time.strftime('%Y-%m-%d %H:%M:%S'), 'files': {}}
for rel, src in FILES.items():
    d = GAME / rel
    if d.exists():
        b = BK / rel; b.parent.mkdir(parents=True, exist_ok=True)
        if not b.exists():
            shutil.copy2(d, b)
        old = sha(d)[:8]
        d.unlink()
    else:
        old = None
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)
    assert sha(d) == sha(src)
    rep['files'][rel] = {'before': old, 'after': sha(d)[:8]}
(W / 'qa/install_play.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(rep, ensure_ascii=False, indent=1))
