# Performance methodology

Run the deterministic analysis benchmark with the repository environment:

```bash
PYTHONPATH=src python tools/benchmark.py --iterations 2000
```

The benchmark warms the parser for 20 calls, then measures 2,000 complete
traceback parse, source-map, explanation, and conservative suggestion operations.
It reports median and p95 wall-clock latency plus Python allocations observed by
`tracemalloc`. Results are machine-specific and should not be treated as service
latency or a cross-machine guarantee.

## Verified local result

Environment: Apple Silicon macOS, CPython 3.14.5. Recorded 2026-10-27.

| Run | Iterations | Median | p95 | Peak traced allocation |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 2,000 | 0.1878 ms | 0.2144 ms | 94.9 KiB |
| 2 | 2,000 | 0.1896 ms | 0.2045 ms | 94.9 KiB |
| 3 | 2,000 | 0.1920 ms | 0.2659 ms | 94.9 KiB |

These are baseline measurements for the audited implementation. No speedup claim is
made because this milestone added a write-safety workflow rather than changing the
analysis hot path.
