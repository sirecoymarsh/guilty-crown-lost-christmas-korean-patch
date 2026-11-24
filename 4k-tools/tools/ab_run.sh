#!/bin/bash
# 4배 켬/끔을 번갈아 돌리고 마지막 기록 줄을 모은다. bash ab_run.sh <접두> <초>
P=$1; S=${2:-300}; cd /f/AI/gclx-4k/tools
for r in "${P}a" "${P}b --art-off" "${P}c" "${P}d --art-off"; do
  set -- $r
  python -X utf8 run_test.py $r --seconds $S --shot-ms 30000 --keys > /dev/null 2>&1
  f=/f/AI/gclx-4k/hires/art.log; [ "$2" = "--art-off" ] && f=/f/AI/gclx-4k/hires/art-off.log
  mv $f /f/AI/gclx-4k/testrun/$1/ 2>/dev/null
  echo "$1 $2 $(grep '^shot' /f/AI/gclx-4k/testrun/$1/$(basename $f) | tail -1) | $(python -X utf8 -c "import json;r=json.load(open(r'F:/AI/gclx-4k/testrun/$1/report.json',encoding='utf-8'));print('dialogs',r.get('dialogs_closed'),'focus',r.get('focus_returned'))")"
done
