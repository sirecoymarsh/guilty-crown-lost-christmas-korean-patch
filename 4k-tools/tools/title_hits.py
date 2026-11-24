"""타이틀 단추의 누르는 자리 그림(cg/sys/title/*-000.png) 크기·불투명 범위를 판본별로 본다(큰 묶음은 mmap 으로).
python -X utf8 title_hits.py <cg.npa> ..."""
import io, mmap, sys
from pathlib import Path
sys.path.insert(0, r'P:\AI\gclx-fix\tools')
import npa_adapter
from PIL import Image


class MNPA(npa_adapter.NPA):
    def __init__(self, path):
        f = open(path, 'rb')
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        orig = Path.read_bytes
        Path.read_bytes = lambda self_: mm if str(self_) == str(Path(path)) else orig(self_)
        try:
            super().__init__(path)
        finally:
            Path.read_bytes = orig


if __name__ == "__main__":
  for p in sys.argv[1:]:
      a = MNPA(p)
      print('==', p)
      for e in a.entries:
          n = e['name'].lower().replace('\\', '/')
          if 'sys/title/' in n and n.endswith('-000.png'):
              im = Image.open(io.BytesIO(a.read(e))).convert('RGBA')
              box = im.getchannel('A').point(lambda v: 255 if v else 0).getbbox()
              print(f"  {e['name']:40s} {im.size} 불투명 {box}")
