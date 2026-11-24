"""Summarize only the native game runs used to accept the timing and playback change."""
import json,re
from pathlib import Path
import numpy as np
import soundfile as sf
from compare_clock import analyze,fit,smooth
HERE=Path(__file__).resolve().parent
RUNS=HERE/'runs'
def load(path):return json.loads(path.read_text(encoding='utf8'))
def traces(name):
    p=RUNS/name
    rep=load(p/'report.json')
    assert not rep.get('error') and max(rep['audio_peak'].values())>.03
    return (p/'profile/trace.log').read_text()
def main():
    for name in ('clock-fixed-ends','final-song-ends','natural-clock'):traces(name)
    before=load(RUNS/'final-song-ends/timing-result.json')
    after=load(RUNS/'clock-fixed-ends/timing-result.json')
    assert len(before)==len(after)==10
    before_leads=[x['peak_vs_source'][0]['cursor_minus_audio_at_update_ms'] for x in before.values()]
    metrics=[]
    for tr,row in after.items():
        full=row['peak_vs_source'][0]
        assert full['correlation']>.52 and abs(full['cursor_minus_audio_at_update_ms'])<65
        assert -50<=row['audio_minus_planned_at_clear_ms']<=270
        metrics.append(row['audio_minus_planned_at_clear_ms'])
    natural=RUNS/'natural-clock';meter=np.loadtxt(natural/'meter.csv',delimiter=',',skiprows=1)
    log=(natural/'profile/trace.log').read_text()
    points=[(int(t),int(ms)) for t,ms in re.findall(r'(\d+) tracefin_T5_C\d+_M(\d+)',log)]
    y,sr=sf.read(HERE.parent/'audio/lxbgm14.ogg',dtype='float32',always_2d=True);n=sr//100
    ref=smooth(np.max(np.abs(y[:len(y)//n*n].reshape(-1,n*2)),axis=1))
    samples=[]
    for sec in (0,8,16,24,32):
        a=points[0][0]+1100+sec*1000;b=a+5200
        guess=points[0][1]/1000+(a-points[0][0])/1000
        co,pos=fit(ref,meter[:,0],meter[:,1],a,b,guess)
        off=round(float(np.median([ms-1000*pos-(t-a) for t,ms in points if a<=t<=b])))
        assert co>.75 and 840<off<1000
        samples.append({'reference_s':pos,'correlation':co,'decoder_lead_ms':off})
    expected=load(HERE/'lookup-expected.json')
    modern=traces('clock-fixed-play')
    got=[list(map(int,m)) for m in re.findall(r'tracetbl_(\d+)_(\d+)_(\d+)',modern)]
    assert got==expected and len(got)==20
    cues=[c for c in load(HERE/'accepted.json')['cues'] if c['track']=='lxbgm14']
    def at(ms):return next((q['id'] for q in cues if q['start']<=ms<q['end']),0)
    positions={'story':0,'sound':0}
    for cue,ms,y in re.findall(r'traceclock_C(\d+)_M(\d+)_Y(\d+)',modern):
        cue,ms,y=map(int,(cue,ms,y))
        if y not in (14,484):continue
        assert at(ms)==cue,(cue,ms,y)
        positions['sound' if y==484 else 'story']+=1
    assert min(positions.values())>=8
    legacy=[list(map(int,m)) for m in re.findall(r'traceaw_L(\d+)_M(\d+)',traces('clock-fixed-slot'))]
    assert len(legacy)>12 and all(at(ms)==cue for cue,ms in legacy)
    assert any(c==182 and ms>35700 for c,ms in legacy) and any(c==183 and ms>46000 for c,ms in legacy)
    out={'all_endings_passed':len(after),'lookup_cases_passed':len(got),'modern_display_samples':positions,
         'legacy_display_samples':len(legacy),'earlier_decoder_lead_ms_range':[min(before_leads),max(before_leads)],
         'earlier_decoder_median_lead_ms':round(float(np.median(before_leads))),
         'no_seek_clock_calibration':samples,'corrected_clock_median_per_song_range_ms':[min(r['peak_vs_source'][0]['cursor_minus_audio_at_update_ms'] for r in after.values()),max(r['peak_vs_source'][0]['cursor_minus_audio_at_update_ms'] for r in after.values())],
         'clear_relative_to_vocal_end_ms':[min(metrics),max(metrics)],'tested_builds':{'ten_endings':'Claude merged engine and latest scenario','ordinary_play_and_saved_slot':'installed-equivalent engine and play scenario'}}
    (HERE/'runtime-verification.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(out)
if __name__=='__main__':main()
