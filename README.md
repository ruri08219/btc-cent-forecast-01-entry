# ruri08 btc-cent forecast

Entry for make.fun `btc-cent-forecast-01`: forecast Bitcoin's US-dollar
price 240 minutes (4 hours) after each checkpoint, as one number per case.

## Model

`main.py` (Python 3.13, stdlib only, no network, deterministic) reads a
case from `$MAKEFUN_INPUT_DIR` (else `/input`) and writes
`{"forecasts": [{"case", "price"}]}` to `$MAKEFUN_OUTPUT_DIR` (else
`/output`): one guess per case.

With `last` the close at the checkpoint and `p60` the close 60 minutes
before it:

```
guess = last + 0.3 * (last - p60)
```

## Why this beats the house baseline

- Under mean absolute error the best point forecast is the conditional
  median. A random walk's median is the last close (the house baseline),
  but BTC's 1-hour trend carries into the next 4 hours on the practice
  set, so a dampened slice of the last hour's move beats persistence.
- Mean reversion to the trailing 24h/72h mean and medians of the last
  closes were all worse than persistence, so neither is used.
- k=0.3 is deliberately moderate: higher k kept improving the 5-case
  mean but only by leaning harder on two trending cases — overfitting
  a 5-case sample.

## Practice result

Scored on the kit's practice cases p00–p04 (actual = next case's
checkpoint close; p05's target is outside the kit):

- persistence baseline: 47,054.7 cents mean error
- this model: 41,123.5 cents mean error (-12.6%)

Official 6-case baseline is 44,521.58 cents.
