import sys
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools')
sys.path.insert(0, r'F:\AI\gclx-4k\release_1121\sound_seek'); sys.path.insert(0, r'F:\AI\gclx-4k\tools'); sys.path.insert(0, r'P:\AI\gclx-fix\tools')
from pathlib import Path
from npa_assets import NPA
import patch_seek as ps
a = NPA(Path(sys.argv[1])); e = {x['name']: x for x in a.entries}
t = ps.rd(a, e['kr_movie.nss']).decode('cp949', 'replace')
Path('kr_movie.new.txt').write_text(t, 'utf-8')
i = t.index('\tif($KM_OK2){'); print(t[i:i+1500]); print('....'); i = t.index('\t\t\tcase km_r01'); print(t[i:i+1400]); i = t.index('function KmCalc'); print(t[i:])
