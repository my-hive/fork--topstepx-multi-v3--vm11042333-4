"""Exp21: 30m ORB, one attempt/day, post-2019 liquid micros only: MNQ MES MYM M2K (US equity)
+ MCL (crude). Stop = opposite range extreme, $300 risk, cap 8/symbol (4.0 std eq max).
Equity side: LONG ONLY (screen exp12: downside ORB breaks fade in ES/NQ both 2010-18 and
2019-23 - dip-buying / dealer flows; upside breaks continue with equity risk premium).
MCL: both sides (no structural drift in crude; exp18 MCL both sides net +2.0k).
Several concurrent $300 streams raise daily variance needed for 30-session target.
Gap while holding: evaluator flattens -> stay flat rest of session.
"""
import numpy as np

ENTRY_AFTER = 9 * 3600 + 35 * 60   # 09:35 CT first eligible entry signal bar
EXIT_AT = 14 * 3600 + 55 * 60      # flat target at 14:55 bar
RNG_LO, RNG_HI = 30600, 34200      # range bars 08:30..09:00 CT
MIN_RANGE_BARS = 25
MAX_RISK = 300.0
PV = {'MNQ': 2.0, 'MES': 5.0, 'MYM': 0.5, 'M2K': 5.0, 'MCL': 100.0}
LONG_ONLY = {'MNQ', 'MES', 'MYM', 'M2K'}
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
