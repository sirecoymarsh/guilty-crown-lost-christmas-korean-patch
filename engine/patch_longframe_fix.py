from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\hires_art.inc'); s = p.read_text('utf-8')
bad = 'frame=%llu\n",ms,pfFrame*1000.0/f.QuadPart,'
assert s.count(bad) == 1
s = s.replace(bad, 'frame=%llu\\n",ms,ourMs,')
old = '{double our=pfFrame*1000.0/f.QuadPart;if(our>16)++pfOver16;if(our>50)++pfOver50;'
assert s.count(old) == 1
s = s.replace(old, 'double ourMs=pfFrame*1000.0/f.QuadPart;{double our=ourMs;if(our>16)++pfOver16;if(our>50)++pfOver50;')
p.write_text(s, 'utf-8'); print('ok')
