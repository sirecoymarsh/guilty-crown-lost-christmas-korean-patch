"""vn-qol 선택표에 「한국어 패치 1.0 에 이미 있음」을 표시해 P:\\AI\\gclx-qol 로 옮긴다(사용자가 앱에서 열 수 있게)."""
import re
from pathlib import Path
src = Path(r'Y:\AI\claude-work\gclx-qol\편의기능_선택.md')
dst = Path(r'P:\AI\gclx-qol\편의기능_선택.md'); dst.parent.mkdir(parents=True, exist_ok=True)
DONE = {   # 끔 + 표시
    'hd-text': '한국어 패치 1.0 에 이미 있음(대사·메뉴 글자 4K)',
    'hd-art-switch': '한국어 패치 1.0 에 이미 있음(F8 · 환경 설정 셋째 쪽)',
    'backlog-jump': '한국어 패치 1.0 에 이미 있음(밑줄 대사 누르기 — 묻는 창은 없음)',
    'music-room': '한국어 패치 1.0 에 이미 있음(타이틀 「사운드」)',
    'recollection-thumbs': '한국어 패치 1.0 에 이미 있음(타이틀 「회상」: 장면 칸 그림·줄거리)',
    'qa-chart': '한국어 패치 1.0 에 이미 있음(회상의 단계별 장면 표 + 모두 열기)',
}
PART = {   # 켠 채 덧붙임
    'pc-settings': '일부 있음: 원래 환경 설정 꼴의 셋째 쪽(화질·초당 프레임) — 새 설정은 여기에 더함',
    'qa-unlock': '일부 있음: 회상·사운드 「모두 열기」 — 원작 CG 라이브러리(결말 뒤)·결말은 아직',
    'voice-comfort': '일부 원작에 있음: 「대사 표시와 음성 동기화」 — 배경음 줄이기는 없음',
    'backlog-scroll': '원작 대화 기록에 스크롤 막대 있음 — 끌기·Page Up/Down 은 확인 전',
}
out = []
for line in src.read_text('utf-8').splitlines():
    m = re.match(r'- \[(.)\] `([a-z0-9-]+)` (.*)$', line)
    if m and m.group(2) in DONE:
        line = f'- [ ] `{m.group(2)}` {m.group(3)} — **{DONE[m.group(2)]}**'
    elif m and m.group(2) in PART:
        line = f'{line} — *{PART[m.group(2)]}*'
    out.append(line)
text = '\n'.join(out) + '\n'
text = text.replace('원작에 이미 있는 것:', '원작에 이미 있는 것(키 S 저장 화면·L 불러오기·A 자동·Ctrl 건너뛰기·B 대화 기록·C 설정·F 전체 화면·J 직전 선택지·T 처음으로, 캐릭터별 음성, 대화 기록 음성):', 1)
dst.write_text(text, encoding='utf-8')
print(dst, sum(1 for l in out if l.startswith('- [x]')), 'checked')
