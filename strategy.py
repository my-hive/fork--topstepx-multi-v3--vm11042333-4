"""Exp5: Market intraday momentum (last half hour), equity micros.

Mechanism (Gao-Han-Li-Zhou 2018; Baltussen-Da-Lammers-Martens 2021): dealer
gamma hedging and late-day rebalancing make the 14:30-15:00 CT return follow
the sign of the return from prior RTH close (14:59 bar) to 14:29 today.
One entry per symbol per day at 14:30 CT close (fills 14:31), flat at 14:59 bar
close (fills 15:00 open). Stop = 1.5x trailing 20-session mean 14:30-15:00 range,
size = floor($300 / (stop * $/pt)), cap 10.
"""
import numpy as np

T_SIG = 14 * 3600 + 29 * 60      # 14:29 bar close = signal
T_EXIT = 14 * 3600 + 59 * 60     # 14:59 bar -> target 0
MAX_RISK = 300.0
PV = {'MES': 5.0, 'MNQ': 2.0}

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
        prev_close = np.nan      # prior session 14:59 close
        today_close = np.nan
        ranges = []
        w_hi, w_lo = -np.inf, np.inf
        pos, stop = 0, 0.0
        for i in range(n):
            if i == 0 or sess[i] != sess[i - 1]:
                if np.isfinite(w_hi) and np.isfinite(w_lo):
                    ranges.append(w_hi - w_lo)
                if np.isfinite(today_close):
                    prev_close = today_close
                today_close = np.nan
                w_hi, w_lo = -np.inf, np.inf
                pos = 0
            s = sec[i]
            if T_SIG < s <= T_EXIT:
                w_hi = max(w_hi, high[i]); w_lo = min(w_lo, low[i])
            if s == T_EXIT:
                today_close = close[i]
            if pos != 0:
                if s >= T_EXIT or (pos > 0 and low[i] <= stop) or (pos < 0 and high[i] >= stop):
                    pos = 0
                out[i] = pos
                continue
            if s == T_SIG and np.isfinite(prev_close) and len(ranges) >= 20:
                r = close[i] - prev_close
                dist = 1.5 * float(np.mean(ranges[-20:]))
                if r == 0 or dist <= 0:
                    continue
                size = int(min(10, MAX_RISK / (dist * PV[symbol])))
                if size >= 1:
                    d = 1 if r > 0 else -1
                    pos = d * size
                    stop = close[i] - d * dist
                    out[i] = pos
        result[symbol] = out
    return result
