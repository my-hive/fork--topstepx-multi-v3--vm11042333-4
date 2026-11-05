"""Exp2: Overnight drift capture on equity micros (MES MNQ M2K).

Mechanism: overnight-return anomaly (Lou-Polk-Skouras) - US equity index futures
drift up 17:00->08:30 CT on persistent passive/NAV flows. One session ON leg
per day, no intraday churn. Position: risk $300 with stop = lagged 20-bar ATR
(1-min) in dollars, capped 3 contracts (also keeps DLL adverse < lock).
Entry: first allowed ON bar (17:00 CT+). Exit: last bar before 08:30 CT.
"""
import numpy as np

CT_EXIT = 8 * 3600 + 25 * 60   # flatten target by 08:25 CT bar
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
        close = df.close.to_numpy(); high = df.high.to_numpy(); low = df.low.to_numpy()
        sec = df.ct_sec.to_numpy()
        tr = high - low
        # lagged 20-bar average TR (causal: bars i-20..i-1)
        csum = np.concatenate(([0.0], np.cumsum(tr)))
        atr = (csum[np.arange(n)] - csum[np.maximum(np.arange(n) - 20, 0)]) / np.minimum(np.arange(n), 20)
        stop_dollars = 2.0 * atr * PV[symbol]
        size = np.where(stop_dollars > 0, np.floor(MAX_RISK / np.maximum(stop_dollars, 1e-9)), 0.0)
        size = np.clip(size, 0, 3).astype(np.int64)
        lag_size = np.roll(size, 1); lag_size[0] = 0
        want = np.zeros(n, dtype=np.int64)
        on = (sec >= 17 * 3600) | (sec < 9 * 3600)
        want = np.where(on, lag_size, 0)
        result[symbol] = want
    return result
