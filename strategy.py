"""Exp4: Opening-range breakout (ORB) on equity micros MES MNQ M2K.

Literature-grounded intraday momentum: establish 30-minute opening range
(08:30-09:00 CT); enter on first 1-min close beyond range extreme at/after
09:35 CT (keeps entry-time diversity share low); stop at opposite range
extreme; flat by 14:55. One attempt per day (no re-entry after stop).
Size: $300 risk / (stop_dist * point_value), capped 3.
Economic basis: overnight information assimilates into directional RTH
continuation; volatility clustering after open makes breakouts informative.
"""
import numpy as np

ENTRY_AFTER = 9 * 3600 + 35 * 60   # 09:35 CT first eligible entry signal bar
EXIT_AT = 14 * 3600 + 55 * 60      # flat target at 14:55 bar
RNG_LO, RNG_HI = 30600, 34200      # range bars 08:30..09:00 CT
MIN_RANGE_BARS = 25
MAX_RISK = 300.0
PV = {'MES': 5.0, 'MNQ': 2.0, 'M2K': 5.0}

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
        pos = 0; stop_px = 0.0; entered = False
        r_hi = -1e18; r_lo = 1e18; r_seen = 0
        for i in range(n):
            s = sec[i]
            if i == 0 or sess[i - 1] != sess[i]:
                r_hi, r_lo, r_seen = -1e18, 1e18, 0
                pos = 0; stop_px = 0.0; entered = False
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
                sz = int(min(3, MAX_RISK / (dist * PV[symbol])))
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
