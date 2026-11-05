"""Exp17 (exp16 + gap-abort only while holding): 30m ORB both sides, portfolio of liquid micros (equity MNQ MES MYM, energy MCL,
metals MGC). Same rule everywhere; point values are contract metadata.
Mechanism: open-hour information flow -> directional continuation; several weakly
correlated $300-risk streams raise daily variance/edge vs single market (exp15 sd 164).
Gap abort: evaluator flattens on any missing minute; after a gap the symbol stays
flat for the session (prevents re-entry churn seen in exp2/exp8).
Per-symbol cap 8 contracts (0.8 std eq) x 5 symbols = 4.0 <= 5.0 exposure.
"""
import numpy as np

ENTRY_AFTER = 9 * 3600 + 35 * 60   # 09:35 CT first eligible entry signal bar
EXIT_AT = 14 * 3600 + 55 * 60      # flat target at 14:55 bar
RNG_LO, RNG_HI = 30600, 34200      # range bars 08:30..09:00 CT
MIN_RANGE_BARS = 25
MAX_RISK = 300.0
PV = {'MNQ': 2.0, 'MES': 5.0, 'MYM': 0.5, 'MCL': 100.0, 'MGC': 10.0}
CAP = 8

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
        pos = 0; stop_px = 0.0; entered = False
        r_hi = -1e18; r_lo = 1e18; r_seen = 0
        for i in range(n):
            s = sec[i]
            if i == 0 or sess[i - 1] != sess[i]:
                r_hi, r_lo, r_seen = -1e18, 1e18, 0
                pos = 0; stop_px = 0.0; entered = False
            if pos and t[i] - t[i - 1] != 60_000_000_000:
                pos = 0                          # gap while holding: evaluator flattened; stay flat
            if RNG_LO <= s < RNG_HI:
                r_hi = max(r_hi, high[i]); r_lo = min(r_lo, low[i]); r_seen += 1
            if pos == 0:
                if entered or r_seen < MIN_RANGE_BARS or s < ENTRY_AFTER or s >= EXIT_AT:
                    continue
                if close[i] > r_hi:
                    dirn, stop_px = 1, r_lo
                elif close[i] < r_lo:
                    dirn, stop_px = -1, r_hi
                else:
                    continue
                dist = abs(close[i] - stop_px)
                if dist <= 0:
                    continue
                sz = int(min(CAP, MAX_RISK / (dist * PV[symbol])))
                if sz >= 1:
                    pos = dirn * sz; entered = True
                    out[i] = pos
            else:
                if s >= EXIT_AT or (pos > 0 and low[i] <= stop_px) or (pos < 0 and high[i] >= stop_px):
                    out[i] = 0
                    pos = 0
                else:
                    out[i] = pos
        result[symbol] = out
    return result
