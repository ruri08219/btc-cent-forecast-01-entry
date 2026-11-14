#!/usr/bin/env python3
"""btc-cent-forecast-01 entry: last close plus dampened 1-hour momentum.

Model: guess = last + 0.3 * (last - close 60 minutes ago).

Why: under mean absolute error the best point forecast is the
conditional median. A random walk's median is the last close (the house
baseline), but BTC's 1-hour trend carries into the next 4 hours on the
practice set: adding a dampened slice of the last hour's move beats
persistence on 4 of 5 scored practice cases. Mean reversion to the
trailing 24h/72h mean and medians of the last closes were all worse
than persistence, so neither is used. k=0.3 is deliberately moderate:
higher k kept improving the 5-case mean but only by leaning harder on
two trending cases — overfitting a 5-case sample.

Practice (p00-p04, actual = next case's checkpoint close):
  persistence baseline  47,054.7 cents mean error
  this model            41,123.5 cents mean error  (-12.6%)
Official 6-case baseline is 44,521.58 cents; p05's target is outside
the kit, so it is not scored here.

Stdlib only, no network, deterministic (no randomness, no clock).
Reads $MAKEFUN_INPUT_DIR (else /input), writes $MAKEFUN_OUTPUT_DIR
(else /output): one <id>.out per <id>.in, {"forecasts":[{"case","price"}]}.
"""

import json
import os

INPUT_DIR = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
OUTPUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")

LAG_MINUTES = 60
K = 0.3


def guess(prices):
    if not prices:
        raise ValueError("market has no prices")
    last = prices[-1]
    if len(prices) <= LAG_MINUTES:
        return last
    return last + K * (last - prices[-1 - LAG_MINUTES])


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    inputs = sorted(f for f in os.listdir(INPUT_DIR) if f.endswith(".in"))
    for fname in inputs:
        cid = fname[: -len(".in")]
        with open(os.path.join(INPUT_DIR, fname), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        markets = case["markets"]
        if len(markets) != 1:
            raise ValueError("%s holds %d markets, expected 1" % (fname, len(markets)))
        price = guess(markets[0]["prices"])
        if not (0.0 < price < 10_000_000.0):
            raise ValueError("guess %r out of range" % price)
        with open(os.path.join(OUTPUT_DIR, cid + ".out"), "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"forecasts": [{"case": cid, "price": price}]}) + "\n")


if __name__ == "__main__":
    main()
