"""n2hd_gpu_v8.cpp: 4배 그림 비동기 풀기·파일별 캐시를 잇는 곳(hires_art.inc 의 artRelease/artFrameEnd/artFrameTiming)과 시험 기록 칸. 한 번만 돌린다."""
from pathlib import Path
p = Path(r'F:\AI\gclx-4k\engine\src\n2hd_gpu_v8.cpp'); s = p.read_text('utf-8')


def rep(old, new):
    global s
    assert s.count(old) == 1, old[:70]
    s = s.replace(old, new)


rep('static void releaseGpu(){Backlog::release();', 'static void releaseGpu(){Backlog::release();artRelease();')
rep('{Guard guard;if(begun){dev->EndScene();begun=false;}++frames;', '{Guard guard;if(begun){dev->EndScene();begun=false;}++frames;artFrameEnd();')
rep('++presents;testShot();return 1;', '++presents;artFrameTiming();testShot();return 1;')
rep('stale=%llu decode_ms_max=%llu\\n",shots-1,now,(unsigned long long)presents,(unsigned long long)artLoads,(unsigned long long)artMatched,(unsigned long long)artUploads,(unsigned long long)artFails,(unsigned long long)artStale,(unsigned long long)artDecodeMsMax);',
    'stale=%llu decode_ms_max=%llu upload_ms_max=%llu late=%llu cache_mb=%llu long50=%llu long100=%llu\\n",shots-1,now,(unsigned long long)presents,(unsigned long long)artLoads,(unsigned long long)artMatched,(unsigned long long)artUploads,(unsigned long long)artFails,(unsigned long long)artStale,(unsigned long long)artDecodeMsMax,(unsigned long long)artUploadMsMax,(unsigned long long)artLate,(unsigned long long)(artCacheBytes>>20),(unsigned long long)artLongFrames50,(unsigned long long)artLongFrames100);')
p.write_text(s, 'utf-8')
print('ok')
