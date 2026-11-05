"""Exp25: exp23 minus M2K (illiquid: 15-150 missing ON minutes/day, worst cost/vol of equity micros;
flagged a priori in exp2). Both sides everywhere.
Exp24 note: exp23 with MES long-only. Screen exp12 (full ES, 2010-18 AND 2019-23): ES downside
ORB breaks lose (-0.047R/-0.042R gross), upside continue (+0.031R/+0.055R).
Exp23: exp4 rule (30m ORB both sides, 1 attempt/day, stop opposite extreme, $300 risk,
cap 3/symbol) on MES MNQ M2K + MCL, with gap-abort while holding.
exp4 was the only gate-passing variant (score .016); MCL added as a non-equity stream
(positive in exp18/exp21, 2021-23). Gap abort removes evaluator re-entry churn (M2K gaps).
"""
import numpy as np

ENTRY_AFTER = 9 * 3600 + 35 * 60   # 09:35 CT first eligible entry signal bar
EXIT_AT = 14 * 3600 + 55 * 60      # flat target at 14:55 bar
RNG_LO, RNG_HI = 30600, 34200      # range bars 08:30..09:00 CT
MIN_RANGE_BARS = 25
MAX_RISK = 300.0
PV = {'MES': 5.0, 'MNQ': 2.0, 'MCL': 100.0}
LONG_ONLY = set()
CAP = 3

def signals(panel):
    result = {}
    for symbol, df in panel.items():
        n = len(df)
        out = np.zeros(n, dtype=np.int64)
        if symbol not in PV:
            result[symbol] = out
            continue
        high = df.high.to_numpy(); low = df.low.to_numpy(); close = df.close.to_numpy()
        sec = df.ct_sec.to_numpy(); sess = df.session.astype(str).to_numpy()
        t = df.index.as_unit('ns').asi8
        pos = 0; stop_px = 0.0; entered = False; tries = 0
        r_hi = -1e18; r_lo = 1e18; r_seen = 0
        for i in range(n):
            s = sec[i]
            if i == 0 or sess[i - 1] != sess[i]:
                r_hi, r_lo, r_seen = -1e18, 1e18, 0
                pos = 0; stop_px = 0.0; entered = False; tries = 0
            if pos and t[i] - t[i - 1] != 60_000_000_000:
                pos = 0                          # gap while holding: evaluator flattened; stay flat
            if RNG_LO <= s < RNG_HI:
                r_hi = max(r_hi, high[i]); r_lo = min(r_lo, low[i]); r_seen += 1
            if pos == 0:
                if tries >= 1 or r_seen < MIN_RANGE_BARS or s < ENTRY_AFTER or s >= EXIT_AT:
                    continue
                if close[i] > r_hi:
                    dirn, stop_px = 1, r_lo
                elif close[i] < r_lo and symbol not in LONG_ONLY:
                    dirn, stop_px = -1, r_hi
                else:
                    continue
                dist = abs(close[i] - stop_px)
                if dist <= 0:
                    continue
                sz = int(min(CAP, MAX_RISK / (dist * PV[symbol])))
                if sz >= 1:
                    pos = dirn * sz; tries += 1
                    out[i] = pos
            else:
                if s >= EXIT_AT or (pos > 0 and low[i] <= stop_px) or (pos < 0 and high[i] >= stop_px):
                    out[i] = 0
                    pos = 0
                else:
                    out[i] = pos
        result[symbol] = out
    return result
