"""Exp8: Cross-asset first-hour range breakout (research screen across classes).

Mechanism: US cash-open hour (08:30-09:30 CT) concentrates macro data and
order flow for all CME products; a break of that hour's range afterwards
signals informed directional flow that continues into the afternoon
(intraday time-series momentum). Same rule for every market:
range = 08:30-09:29 bars, entry on first close beyond range 09:30-12:59,
stop = opposite range extreme, flat 14:55. One trade/market/day.
Size = floor($300 / (stop distance * $/pt)), cap 5; skip if <1.
Point values from contract specs (metadata, not tuned).
"""
import numpy as np

RNG_LO, RNG_HI = 30600, 34200           # 08:30..09:29 CT
ENTRY_END = 13 * 3600
EXIT_AT = 14 * 3600 + 55 * 60
MIN_BARS = 40
MAX_RISK = 300.0
# (dollars/point, evaluator standard-equivalent weight)
SPEC = {'MES': (5.0, .1), 'MNQ': (2.0, .1), 'MYM': (0.5, .1), 'M2K': (5.0, .1), 'MGC': (10.0, .1),
        'SIL': (1000.0, .2), 'M6E': (12500.0, .1), 'M6A': (10000.0, .1), 'M6B': (6250.0, .1)}
BUDGET = 4.9   # aggregate exposure cap 5.0, split equally over traded symbols present

def signals(panel):
    result = {}
    for symbol, df in panel.items():
        n = len(df)
        out = np.zeros(n, dtype=np.int64)
        if symbol not in SPEC:
            result[symbol] = out
            continue
        pv, w = SPEC[symbol]
        cap = int(BUDGET / len(SPEC) / w)
        high = df.high.to_numpy(); low = df.low.to_numpy(); close = df.close.to_numpy()
        sec = df.ct_sec.to_numpy(); sess = df.session.astype(str).to_numpy()
        pos = 0; stop = 0.0; done = False
        hi = -np.inf; lo = np.inf; cnt = 0
        for i in range(n):
            s = sec[i]
            if i == 0 or sess[i] != sess[i - 1]:
                hi, lo, cnt = -np.inf, np.inf, 0
                pos, done = 0, False
            if RNG_LO <= s < RNG_HI:
                hi = max(hi, high[i]); lo = min(lo, low[i]); cnt += 1
                continue
            if pos:
                if s >= EXIT_AT or (pos > 0 and low[i] <= stop) or (pos < 0 and high[i] >= stop):
                    pos = 0
                out[i] = pos
                continue
            if done or cnt < MIN_BARS or not (RNG_HI <= s < ENTRY_END):
                continue
            if close[i] > hi:
                d, stop = 1, lo
            elif close[i] < lo:
                d, stop = -1, hi
            else:
                continue
            done = True
            size = int(min(cap, MAX_RISK / (abs(close[i] - stop) * pv)))
            if size >= 1:
                pos = d * size
                out[i] = pos
        result[symbol] = out
    return result
