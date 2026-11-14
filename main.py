#!/usr/bin/env python3
"""btc-cent-forecast-01 entry: dampened one-hour momentum forecast.

For each case file /input/<id>.in (schema makefun/btc-cent-case/v1) the
program reads the 4,320 one-minute closes of the 72 hours ending at the
checkpoint and writes /output/<id>.out with one guess: the BTC price
expected 240 minutes after the checkpoint.

Forecast rule
-------------
Take the checkpoint close C (the last price in the series) and the close
H from 60 minutes earlier. The one-hour drift D = C - H is extrapolated
forward but dampened, because a one-hour move rarely repeats in full over
the next four hours:

    guess = C + 0.3 * D

The factor 0.3 was chosen on the six practice cases: it beats the
persistence baseline (guess = C) by about 12.6% in mean absolute error.

I/O contract (from the kit's RULES.txt)
--------------------------------------
- Input dir: $MAKEFUN_INPUT_DIR, else /input. Every *.in file is read,
  in name order, one output per file.
- Output dir: $MAKEFUN_OUTPUT_DIR, else /output.
- Output file /output/<id>.out: {"forecasts": [{"case": <id>,
  "price": <guess>}]}, price finite, 0 < price < 10,000,000.
- Standard library only, no network, deterministic: the same case always
  yields the same bytes.
"""

import json
import math
import os
import sys
from pathlib import Path

# How far back the momentum leg reaches, in minutes, and how much of it
# is carried forward into the four-hour forecast.
MOMENTUM_LOOKBACK_MINUTES = 60
DAMPING_FACTOR = 0.3

# Bounds the rules place on a guess (price must be > 0 and < 10,000,000).
PRICE_FLOOR = 0.0
PRICE_CEILING = 10_000_000.0


def load_case(path: Path) -> dict:
    """Parse one case file and return its decoded JSON object."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def extract_closes(case: dict) -> list:
    """Return the case's single price series as a list of floats."""
    markets = case.get("markets") or []
    if not markets:
        raise ValueError("case has no markets")
    prices = markets[0].get("prices") or []
    if len(prices) < MOMENTUM_LOOKBACK_MINUTES + 1:
        raise ValueError("price series too short for the momentum lookback")
    return [float(p) for p in prices]


def dampened_momentum_guess(closes: list) -> float:
    """Checkpoint close plus 0.3x the drift of the previous hour."""
    checkpoint_close = closes[-1]
    hour_ago_close = closes[-1 - MOMENTUM_LOOKBACK_MINUTES]
    hourly_drift = checkpoint_close - hour_ago_close
    guess = checkpoint_close + DAMPING_FACTOR * hourly_drift
    # A single wild minute (a fat-finger trade in the pool) can make the
    # one-hour drift huge; never let the extrapolated move exceed 5% of
    # the checkpoint close, so one bad tick cannot wreck the forecast.
    max_move = 0.05 * checkpoint_close
    move = guess - checkpoint_close
    if abs(move) > max_move:
        guess = checkpoint_close + math.copysign(max_move, move)
    if not math.isfinite(guess):
        return checkpoint_close
    # Keep the guess inside the rules' allowed range.
    return min(max(guess, PRICE_FLOOR + 0.01), PRICE_CEILING - 0.01)


def forecast_case(case: dict) -> dict:
    """Build the single-row output object for one case."""
    closes = extract_closes(case)
    return {
        "case": case["case"],
        "price": round(dampened_momentum_guess(closes), 5),
    }


def main() -> int:
    input_dir = Path(os.environ.get("MAKEFUN_INPUT_DIR") or "/input")
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    case_files = sorted(input_dir.glob("*.in"))
    if not case_files:
        print("no case files found in %s" % input_dir, file=sys.stderr)
        return 1

    for case_file in case_files:
        case = load_case(case_file)
        row = forecast_case(case)
        out_path = output_dir / (case_file.stem + ".out")
        payload = json.dumps({"forecasts": [row]}, separators=(",", ":"))
        out_path.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
