# pinball-bench (real, 1280x720, marker pinball-d220-l2-i1 @ 220 dpi)

Errors (px, mm, deg) cover every valid frame; ok = valid pose with mean corner error < 5 px. lock = frames from sequence start to the first valid pose.

## native threads=1 — track share 99.7%, trackTimeShare 99.6%

| group | n | excl | valid% | ok% | med px | p90 px | med mm | med deg | lost | lock med/max | jitter px | det ms p50/p95 | trk ms p50/p95 | total ms p50/p95/max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 291 | 7 | 100 | 49 | 5.09 | 9.25 | - | - | 0 | 0/0 | 4.04 | 73.4/73.4 | 1.2/1.5 | 1.2/1.5/73.4 |

## native threads=-1 — track share 99.7%, trackTimeShare 99.6%

| group | n | excl | valid% | ok% | med px | p90 px | med mm | med deg | lost | lock med/max | jitter px | det ms p50/p95 | trk ms p50/p95 | total ms p50/p95/max |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| real | 291 | 7 | 100 | 49 | 5.09 | 9.37 | - | - | 0 | 0/0 | 4.01 | 69.2/69.2 | 0.6/0.7 | 0.6/0.7/69.2 |

