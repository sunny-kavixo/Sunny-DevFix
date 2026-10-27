"""Small reproducible latency benchmark for the deterministic analysis path."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc

from sunny_devfix.analysis.insights import build_insights
from sunny_devfix.analysis.source_analysis import analyze_source
from sunny_devfix.analysis.traceback_parser import parse_traceback

SOURCE = "def greet(user_name):\n    return 'hello ' + username\n"
TRACEBACK = (
    "Traceback (most recent call last):\n"
    '  File "app.py", line 2, in greet\n'
    "    return 'hello ' + username\n"
    "NameError: name 'username' is not defined\n"
)


def analyze_once() -> None:
    parsed = parse_traceback(TRACEBACK)
    source = analyze_source(SOURCE, parsed, filename="app.py")
    build_insights(SOURCE, parsed, source)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=2_000)
    args = parser.parse_args()
    if args.iterations < 20:
        parser.error("--iterations must be at least 20")

    for _ in range(20):
        analyze_once()
    tracemalloc.start()
    samples = []
    for _ in range(args.iterations):
        started = time.perf_counter_ns()
        analyze_once()
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    ordered = sorted(samples)
    p95_index = min(len(ordered) - 1, int(len(ordered) * 0.95))
    print(
        json.dumps(
            {
                "iterations": args.iterations,
                "median_ms": round(statistics.median(samples), 4),
                "p95_ms": round(ordered[p95_index], 4),
                "peak_traced_kib": round(peak / 1024, 1),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
