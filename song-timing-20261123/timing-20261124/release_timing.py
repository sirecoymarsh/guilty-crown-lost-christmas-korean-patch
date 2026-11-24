"""Locate the audible decay following a sung line, stopping at the next vocal entrance."""
import math
import numpy as np
from audit import envelope, stable_runs

# Reviewed separately where a repeated backing figure follows the last lexical phrase.
FINAL_RELEASES = {
    'lxbgm01': 240.1, 'lxbgm04': 244.1, 'lxbgm05': 204.0, 'lxbgm12': 253.3,
    'lxbgm14': 224.6, 'lxbgm16': 194.5, 'lxbgm18': 116.1, 'lxbgm19': 200.0,
    'lxsong01': 203.0, 'lxsong02': 207.0,
}

def apply_releases(rows):
    for track, final_end in FINAL_RELEASES.items():
        track_rows = [row for row in rows if row['track'] == track]
        db = envelope(track)
        for row, following in zip(track_rows, track_rows[1:]):
            end = row['new'][1]
            next_start = following['new'][0]
            if next_start - end < .35:
                continue
            idx = round(end * 100)
            cutoff = float(np.clip(row['gate'] - 12, -56, -45))
            if np.median(db[idx-25:idx-3]) < cutoff or np.mean(db[idx:idx+12] > cutoff) < .5:
                continue
            limit = min(round(next_start * 100), idx + 125)
            quiet = stable_runs(db[idx:limit] < cutoff, 20)
            if not quiet or not 6 <= quiet[0][0] <= 95:
                continue
            end = min(next_start, math.ceil((idx + quiet[0][0] + 6) / 10) / 10)
            if end > row['new'][1]:
                row['new'][1] = end
                row['why'].append('audible vocal decay before instrumental gap')
        last = track_rows[-1]
        last['new'][1] = final_end
        last['why'].append('final lyric release including audible decay')
