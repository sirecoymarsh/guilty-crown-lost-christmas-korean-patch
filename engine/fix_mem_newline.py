from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')
bad = 'cache_mb=%u\n",now,(unsigned)(freeAll>>20)'
assert s.count(bad) == 1, s.count(bad)
s = s.replace(bad, 'cache_mb=%u\\n",now,(unsigned)(freeAll>>20)')
p.write_text(s, 'utf-8'); print('ok')
