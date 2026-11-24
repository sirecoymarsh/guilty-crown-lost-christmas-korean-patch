import sys
sys.path.insert(0, r'P:\AI\Codex\projects\guilty-crown-lost-christmas-ui-opening\work\tools'); sys.path.insert(0, r'F:\AI\gclx-4k\tools')
from pathlib import Path
from npa_assets import NPA
a = NPA(Path(r'P:\AI\gclx-codexrun\game\krresume.npa'))
print(len(a.entries), [e['name'] for e in a.entries][:40])
