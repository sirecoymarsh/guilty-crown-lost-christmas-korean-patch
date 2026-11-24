"""2장 영상 게임용 판(mv_lx0201.ngs)을 MPEG-1 로 다시 굽는다(11-23).
- 왜: 코덱스 10-26 명령(11-21 에 자막 한 줄만 바꿔 다시 씀)이 MPEG-1 묶음(-f mpeg)에 MPEG-2 영상(mpeg2video)을 넣었다.
  게임 엔진은 이 파일을 첫 장면에서 멈추고(숨긴 시험 mov_scene0201), 원작 MPEG-2 파일은 아예 건너뛴다. 게임의 다른 영상은
  모두 MPEG-1 이고, 같은 화면을 MPEG-1 로 바꾼 판은 재생된다(mov_scene0201_m1).
- 무엇을: 11-21 명령(movie/logs/command.json)의 입력·자막 그림·필터 그대로, 출력만 게임용 [sd] 하나로 줄이고
  영상 부호화를 한국어 오프닝(mv_op.ngs)과 같은 MPEG-1 12Mbps·VBV 112(1,835,008비트)로. 소리는 설치본 .ngs 의 MP2 그대로.
python -I -X utf8 encode_mpeg1.py → movie_room/fixed/mv_lx0201.ngs
"""
import json, subprocess, hashlib
from pathlib import Path
W = Path(__file__).resolve().parent
M = W.parent / 'movie'
cmd = json.loads((M / 'logs/command.json').read_text('utf-8'))['args']
flt = (M / 'out/filter.txt').read_text('utf-8')
old = ('[b18]split=2[hi][lo];\n[hi]scale=out_color_matrix=bt601:in_range=full:out_range=tv,format=yuv420p[hd];\n'
       '[lo]scale=1024:576:flags=lanczos:out_color_matrix=bt709:in_range=full:out_range=tv,format=yuv420p[sd]')
flt = flt.replace('\r\n', '\n')
assert flt.count(old) == 1, 'filter tail'
flt = flt.replace(old, '[b18]scale=1024:576:flags=lanczos:out_color_matrix=bt709:in_range=full:out_range=tv,format=yuv420p[sd]')
fsd = W / 'fixed/filter_sd.txt'; fsd.parent.mkdir(exist_ok=True); fsd.write_text(flt, 'utf-8')
k = cmd.index('-filter_complex_script')
head = cmd[:k]                                   # ffmpeg · 공통 옵션 · 입력들(자막 그림·깨끗한 바탕·설치본 .ngs)
ai = [i for i, a in enumerate(head) if a.endswith(r'game\dx\mv_lx0201.ngs')]; assert len(ai) == 1
out = W / 'fixed/mv_lx0201.ngs'
args = head + ['-filter_complex_script', str(fsd),
               '-map', '[sd]', '-map', '19:a:0',
               '-c:v', 'mpeg1video', '-b:v', '12M', '-minrate', '12M', '-maxrate', '12M', '-bufsize', '1835008',
               '-g', '15', '-bf', '2', '-threads', '4', '-c:a', 'copy',
               '-fps_mode', 'cfr', '-r:v', '30000/1001', '-enc_time_base:v', '1001/30000', '-f', 'mpeg', '-y', str(out)]
# 입력 19번이 설치본 .ngs 인지(소리 원천) 확인
inputs = [head[i + 1] for i, a in enumerate(head) if a == '-i']
assert inputs[19].endswith(r'game\dx\mv_lx0201.ngs'), inputs[19]
subprocess.run(args, check=True)
print(out.name, out.stat().st_size, hashlib.sha256(out.read_bytes()).hexdigest()[:8])
