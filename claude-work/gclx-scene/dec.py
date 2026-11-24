import sys
from pathlib import Path
# 한 줄씩: 한글(cp949)로 읽히는 줄과 일본어(cp932)로 읽히는 줄을 섞어 읽는다 — 주석·파일 이름은 cp932
b = Path(sys.argv[1]).read_bytes() if Path(sys.argv[1]).exists() else None
