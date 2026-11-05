"""Exp3: Overnight drift with hard stops, liquid micros only (MES MNQ).

Mechanism: overnight equity drift + left-tail cut. Enter first ON bar (17:00 CT),
stop = k * causal 20-session overnight true range (per-symbol), sized so
stop risk <= $300. After a stop, stay flat until next ON window (no re-entry
same session) - avoids churn. Exit all at 08:25 CT bar.
"""
import numpy as np

CT_EXIT = 8 * 3600 + 25 * 60
MAX_RISK = 300.0
PV = {'MES': 5.0, 'MNQ': 2.0}
K_STOP = 0.35   # stop = 35% of typical overnight range

def signals(panel):
    result = {}
    for symbol, df in panel.items():
        n = len(df)
        out = np.zeros(n, dtype=np.int64)
        if symbol not in PV:
            result[symbol] = out
            continue
        close = df.close.to_numpy(); high = df.high.to_numpy(); low = df.low.to_numpy()
        sec = df.ct_sec.to_numpy(); sess = df.session.astype(str).to_numpy()
        on = (sec >= 17 * 3600) | (sec < CT_EXIT)
        # ON high/low per session (causal within session: only bars seen so far)
        pos = 0
        stopped = False
        entry_px = 0.0
        stop_px = 0.0
        on_hi = 0.0; on_lo = 1e18
        ranges = []          # completed-session ON ranges
        for i in range(n):
            s = sess[i]
            if i == 0 or sess[i-1] != s:
                if i > 0 and on_lo < 1e18:
                    ranges.append(on_hi - on_lo)
                on_hi = -1e18; on_lo = 1e18
                stopped = False
            if on[i]:
                on_hi = max(on_hi, high[i]); on_lo = min(on_lo, low[i])
            # decide target for this bar's close -> fills next bar open
            if not on[i] or stopped or len(ranges) < 10:
                continue
            avg_range = float(np.mean(ranges[-20:]))
            if avg_range <= 0:
                continue
            if pos == 0:
                # enter next bar: size from stop budget
                stop_dist = K_STOP * avg_range
                size = int(min(5, MAX_RISK / (stop_dist * PV[symbol])))
                if size >= 1:
                    out[i] = size
                    pos = size
                    entry_px = close[i]
                    stop_px = close[i] - stop_dist
            else:
                if low[i] <= stop_px:
                    out[i] = 0
                    pos = 0
                    stopped = True
                else:
                    out[i] = pos
        # final session range
        result[symbol] = out
    return result
