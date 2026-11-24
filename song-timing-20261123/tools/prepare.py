import os,sys,json,shutil,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(R/'tools'))
from npa_adapter import NPA
arc=NPA(R/'baseline/nss.npa')
for e in arc.entries:
 if e['name'] in ['function.nss','function_lx.nss','kr_sound.nss','0_boot.nss','sys_menu.nss','sys_backlog.nss','sys_config.nss']:
  (R/'nss'/e['name']).write_bytes(arc.read(e))
run=R/'tools/run_test.py'
s=run.read_text('utf-8').replace("RUNS = Path(r'F:\\AI\\gclx-4k\\testrun')", "RUNS = Path(__file__).resolve().parents[1] / 'qa/runs'")
run.write_text(s,'utf-8')
shutil.copy2(R/'baseline/nss.npa',R/'nss/nss.normal.npa')
probe='''#include "nss/function.nss"
chapter main
{
 #SYSTEM_window_full=false;
 $SYSTEM_menu_lock=true;
 CreateColor("bg",1,0,0,1024,576,0x203040);
 CreateBGM("kubgm","lxbgm01");
 SoundPlay("@kubgm",0,1000,true);
 SetLoopPoint("@kubgm",78574,100000);
 SetStream("@kubgm",78574);
 $kr_i=0;
 while($kr_i<120){
  $kr_i+=1;
  $kr_t=PassageTime("@kubgm");
  $kr_r=RemainTime("@kubgm");
  $kr_d=DurationTime("@kubgm");
  $kr_log=String("nss/kr_cmd_trace_%d_%d_%d.png",$kr_t,$kr_r,$kr_d);
  CreateTexture("trace",1,0,0,$kr_log);Delete("trace");
  SetFont("Malgun Gothic",26,FFFFFF,000000,600,AROUND);
  $kr_text=String("P=%d R=%d D=%d",$kr_t,$kr_r,$kr_d);
  Delete("probe_text");CreateText("probe_text",20000,60,420,900,80,$kr_text);
  Request("probe_text",NoLog);Request("probe_text",PushText);
  Wait(250);
 }
 Wait(300000);
}
'''
(R/'nss/nss.probe.npa').write_bytes(arc.pack({'0_boot.nss':probe.encode('ascii')}))
(R/'progress.json').write_text(json.dumps({'task':'sound-mode and in-game bilingual song subtitles','baseline_runtime_sha256':'c00681988fdef9c322a23cc57036751a081a98ce5bf793539afa00330c24026d','baseline_nss_sha256':'53de61c86d404ff06e59405aca1279ba00e152e8d8b82359ba6b7971ba1f7d85','translator_model':'Codex internal','completed':['latest release matched to live copy','9 local source audio tracks extracted','existing PassageTime and script process runtime identified'],'remaining':['confirm native audio timeline and loop position','review and translate 9 tracks','connect subtitles','targeted runtime proof','deliver latest-based patch'],'reuse':'Latest N2System runtime, 4K renderer, archives, hidden muted test harness. No external runtime/code imported.','research':['https://www.nitroplus.co.jp/game/lost_x/outline/music/','https://learn.microsoft.com/en-us/previous-versions/windows/desktop/ee418062(v=vs.85)','https://www.sonymusic.co.jp/jlist/soundtrack/SVWC-70156']},ensure_ascii=False,indent=2),'utf-8')
print('prepared probe')
