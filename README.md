# TopstepX multi-asset v3

Research task. Launch wrapper refuses to start until owner verification creates READY marker.

Read program.md for frozen partitions, candidate limits and safety boundaries. All stages use one-minute OHLCV and the same trusted account evaluator. Historical final block overlaps v1/v2 research and is not fresh OOS.

Only strategy.py is editable. Agent sandbox receives development data at /data/dev and trusted evaluator at /opt/v3-eval. Validator takes source plus selected symbols and returns receipts only. Source must define signals(panel); integer targets, same row count per symbol. Account rules apply jointly across instruments.

Development evaluation inside sandbox:

```bash
python3 /opt/v3-eval/eval/sim.py --data /data/dev --symbols MES MGC --strategy "$PWD/strategy.py" --output report.json --ledger fills.jsonl
```

Choose any available subset in `--symbols` (space-separated). Feature-only symbols must return zero targets. Full universe together can exceed RAM; start with a few markets. Default score is mean of worst three available yearly pass rates, gated by positive pass rate in each available 2020–2023 year and entry diversity. Short histories have fewer eligible years; scores are not automatically comparable evidence of robustness. Inspect years actually covered.

Frozen candidate submission:

```bash
python3 /usr/local/bin/v3-validate --strategy strategy.py --symbols MES,MGC
```

Validation symbols are comma-separated for client. Three distinct source SHA256 reservations per agent total; receipts only, numerical results owner-only. Do not treat accepted submission as profitable or passing.

Optional finalist side-randomization diagnostic: add `--null-seeds 200` to development evaluator. This flips portfolio direction by session while preserving timing, not a full randomized-entry null. No automatic significance pass. Record this limitation.

Reference ledger uses next minute open, adverse intrabar account valuation, estimated per-instrument costs and real integer positions. Micro products are not backfilled before inception. Aggregate size weights/fees are research assumptions; current platform-specific limits and fees need owner review before live use.
