from pathlib import Path
import re,json,io,sys,hashlib
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from npa_adapter import NPA
from npa_build import build
base=R/'baseline/nss.npa';arc=NPA(base)
raw={e['name']:arc.read(e) for e in arc.entries if e['size']>=3}
tracks=['lxbgm01','lxbgm04','lxbgm05','lxbgm12','lxbgm14','lxbgm16','lxbgm18','lxbgm19','lxsong01','lxsong02']
trackid={t:i+1 for i,t in enumerate(tracks)};rows=[]
for l in (R/'data/lyrics.tsv').read_text('utf-8').splitlines():
 if not l.strip() or l.startswith('#'):continue
 t,a,b,source,ko=l.split('|');rows.append(dict(track=t,start=round(float(a)*1000),end=round(float(b)*1000),source=source,ko=ko))
blank=io.BytesIO();Image.new('RGBA',(1024,576),(255,255,255,255)).save(blank,format='PNG')
cache=R/'temp/lyric-render-cache';cache.mkdir(exist_ok=True)
prev={}
if (R/'staging/nss.npa').exists() and (R/'data/lyrics.json').exists():
 old=NPA(R/'staging/nss.npa');oe={e['name']:e for e in old.entries}
 for row in (json.loads((R/'data/lyrics.json').read_text('utf-8'))['cues'] if json.loads((R/'data/lyrics.json').read_text('utf-8')).get('renderer_version')==2 else []):
  if row['track'].startswith('lxsong'):continue
  key=hashlib.sha256(('renderer-r2|'+row['source']+'|'+row['ko']).encode('utf-8')).hexdigest();p=cache/(key+'.png')
  if not p.exists():p.write_bytes(old.read(oe[f'kr_ly_{row["id"]:04d}.png']))
add={};lookup=['function KrLyLookup()','{'];warnings=[]
font=R/'game/fonts/NotoSansKR-VF.ttf'
f1=ImageFont.truetype(str(font),80);f2=ImageFont.truetype(str(font),96)
f1.set_variation_by_axes([500]);f2.set_variation_by_axes([600])
jp=ImageFont.truetype(str(R/'assets/NotoSansCJKjp-Medium.otf'),80)
for i,row in enumerate(rows,1):
 row['id']=i;assert row['end']>row['start'] and row['track'] in trackid
 key=hashlib.sha256((('renderer-r3-jp|' if row['track'].startswith('lxsong') else 'renderer-r2|')+row['source']+'|'+row['ko']).encode('utf-8')).hexdigest();cachefile=cache/(key+'.png')
 if not cachefile.exists():
  im=Image.new('RGBA',(4096,224),(0,0,0,0));d=ImageDraw.Draw(im)
  sf=jp if row['track'].startswith('lxsong') else f1
  w=max(d.textlength(row['source'],font=sf),d.textlength(row['ko'],font=f2))
  if w>3904:warnings.append([i,row['track'],int(w),row['source']])
  d.rounded_rectangle((max(24,2048-w/2-52),4,min(4072,2048+w/2+52),220),radius=24,fill=(0,0,0,160))
  d.text((2048,52),row['source'],font=sf,anchor='mm',fill=(226,238,240,255),stroke_width=5,stroke_fill=(0,0,0,255))
  d.text((2048,153),row['ko'],font=f2,anchor='mm',fill='white',stroke_width=6,stroke_fill='black')
  out=io.BytesIO();im.save(out,format='PNG');cachefile.write_bytes(out.getvalue())
 add[f'kr_ly_{i:04d}.png']=cachefile.read_bytes()
 lookup.append(f' if($KLY_TRACK=={trackid[row["track"]]}&&$KLY_TIME>={row["start"]}&&$KLY_TIME<{row["end"]}){{$KLY_CUE={i};}}')
lookup.append('}')
script=(R/'nss/kr_lyrics.template.nss').read_text('ascii');mapping=[]
for t,ix in trackid.items():
 alias=('lx'+t[-2:].zfill(3)) if t.startswith('lxbgm') else t;aliases=[alias]
 if t=='lxbgm01':aliases+=['lx001a','lx001b']
 if t=='lxbgm04':aliases+=['lx004a','lx004b']
 if t=='lxbgm14':aliases+=['lx014a','lx014b','lx014c','lx014d']
 if t=='lxbgm18':aliases+=['lx018a']
 mapping.append(' if('+ '||'.join('$kly_play=="@'+a+'"' for a in aliases)+'){$KLY_MAP='+str(ix)+';}')
preload=['function KrLyPreload()','{']
for t,ix in trackid.items():
 preload.append(f' if($KLY_TRACK=={ix}){{')
 for row in rows:
  if row['track']!=t:continue
  i=row['id'];n=f'krly_img{i:04d}'
  preload.append(f' CreateTexture("{n}",19500,0,$KLY_Y,"nss/kr_ly_{i:04d}.png");SetAlias("{n}","{n}");SetVertex("{n}",0,0);Zoom("{n}",0,250,250,null,false);Fade("{n}",0,0,null,false);Request("{n}",Lock);Request("{n}",Smoothing);')
 preload.append(' }')
preload.append('}')
show=['function KrLyShow()','{']
for row in rows:
 i=row['id'];show.append(f' if($KLY_CUE=={i}){{Fade("@krly_img{i:04d}",0,1000,null,false);}}')
show.append('}')
script+='\n'+'\n'.join(preload)+'\n'+'\n'.join(show)+'\n' 
script=script.replace(' // TRACK_MAP' ,'\n'.join(mapping))+'\n'+'\n'.join(lookup)+'\n'
sys.path.insert(0,str(R/'timing-20261124'))
from clock_patch import modern as apply_lyric_clock
add['kr_lyrics.nss']=apply_lyric_clock(script.encode('ascii'))
rep={};fn=b'#include "nss/kr_lyrics.nss"\r\n'+raw['function.nss']
for name,param in [('SoundPlay','$SoundPlayName'),('MusicStart','$MusicStartName'),('SoundPlayEF','$SoundPlayName'),('MusicStartEF','$MusicStartName')]:
 pattern=rb'(function '+name.encode()+rb'\([^\n]+\)[\r\n]+\{)(.*?)(\n\})'
 def patch(m):return m[1]+m[2]+b'\r\n\tKrLyPlay('+param.encode()+b');\r\n'+m[3]
 fn,n=re.subn(pattern,patch,fn,flags=re.S);assert n==1,(name,n)
a=fn.index(b'function BGMbase()');pos=fn.index(b'{',a)+1
code='\r\n if($ＢＧＭナット=="kubgm"){ $KLY_KU=0;\r\n'
for t,ix in trackid.items():code+=f' if($音楽データ=="{t}"){{$KLY_KU={ix};}}\r\n'
code+=' }\r\n';fn=fn[:pos]+code.encode('cp932')+fn[pos:]
a=fn.index(b'function SetVolumeEX(');pos=fn.index(b'\n{',a)+2
code='\r\n if($ボリウム==0){KrLyStopFor($SetVolumeName);}\r\n'.encode('cp932')
fn=fn[:pos]+code+fn[pos:]
for signature in re.findall(rb'^function[^\r\n]+',raw['function.nss'],re.M):assert signature in fn,signature
p=fn.index(b'function SetRoll(');q=fn.index(b'function EndMovie()',p)
part=fn[p:q];target='SetVolume($BGM名, 6000, 0, NULL);'.encode('cp932');assert part.count(target)==1
part=part.replace(target,'KrLyStopFor($BGM名);'.encode('cp932')+target)
fn=fn[:p]+part+fn[q:]
rep['function.nss']=fn
lx=raw['function_lx.nss'];p=lx.index(b'function SetVolume_Loop(');q=lx.index(b'\n{',p)+2
parameter=re.search(rb'SetVolume_Loop\(("[^"]+")',lx[p:q])[1]
code='\r\n if($ボリウム==0){KrLyStopFor('.encode('cp932')+parameter+b');}\r\n'
rep['function_lx.nss']=lx[:q]+code+lx[q:]

for name,src in raw.items():
 if not name.endswith('.nss') or not (name.startswith(('lx','kr_','sys_')) or name in ['0_boot.nss','function.nss','function_lx.nss']):continue
 src=rep.get(name,src)
 src=re.sub(rb'(SetVolume\(\s*("@(?:lx[^" ]*|kubgm|\*)")\s*,[^,;]+,\s*0\s*,[^;]+\);)',lambda m:b'KrLyStopFor('+m[2]+b');'+m[1],src)
 if src!=raw[name]:rep[name]=src
rep['0_boot.nss']=rep.get('0_boot.nss',raw['0_boot.nss']).replace(b'$PLACE_title=true;',b'KrLyClear();$PLACE_title=true;')
for k,v in rep.items():(R/'staging'/k).write_bytes(v)
(R/'staging/kr_lyrics.nss').write_bytes(add['kr_lyrics.nss'])
(R/'data/lyrics.json').write_text(json.dumps({'renderer_version':2,'jp_font_version':1,'translator_model':'Codex internal','source':'user-provided game audio; two local STT passes and source-word crosschecks','cues':rows},ensure_ascii=False,indent=2),'utf-8')
(R/'qa/layout-warnings.json').write_text(json.dumps(warnings,ensure_ascii=False,indent=2),'utf-8')
build(base,R/'staging/nss.npa',replace=rep,add=add)
probe=b'''#include "nss/function.nss"
chapter main
{
 #SYSTEM_window_full=false;$SYSTEM_menu_lock=true;
 CreateColor("bg",1,0,0,1024,576,0x203040);
 CreateBGM("kubgm","lxbgm01");SoundPlay("@kubgm",0,1000,true);
 SetLoopPoint("@kubgm",78574,88000);SetStream("@kubgm",78574);
 Wait(18000);KrLyStopFor("@kubgm");SetVolume("@kubgm",0,0,null);
 Wait(300000);
}
'''
probeRep=dict(rep);probeRep['0_boot.nss']=probe
build(base,R/'nss/nss.lyric-probe.npa',replace=probeRep,add=add)
print(json.dumps({'cues':len(rows),'tracks':len(set(x['track'] for x in rows)),'changed_entries':list(rep),'layout_warnings':warnings},ensure_ascii=False))

