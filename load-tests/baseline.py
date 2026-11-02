#!/usr/bin/env python3
"""Dependency-free fixed-workload load test for the Phase 1 Order API."""

import argparse
import json
import statistics
import threading
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def percentile(values, percent):
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * percent / 100
    lower, upper = int(index), min(int(index) + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


class Metrics:
    def __init__(self):
        self.lock = threading.Lock()
        self.latencies_ms = []
        self.errors = 0
        self.requests = 0

    def record(self, latency_ms, error):
        with self.lock:
            self.latencies_ms.append(latency_ms)
            self.requests += 1
            self.errors += int(error)


def request(url, method="GET", body=None):
    request_body = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=request_body, method=method)
    if body is not None:
        request.add_header("Content-Type", "application/json")
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response_body = response.read()
            return (time.perf_counter() - started) * 1000, False, json.loads(response_body) if response_body else {}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return (time.perf_counter() - started) * 1000, True, {}


def worker(base_url, deadline, metrics, worker_id):
    while time.perf_counter() < deadline:
        create_latency, create_error, created = request(
            base_url + "/orders",
            "POST",
            {"customerId": f"load-{worker_id}", "sku": "sku-1", "quantity": 1},
        )
        metrics.record(create_latency, create_error)
        if create_error or "id" not in created:
            continue
        order_id = created["id"]
        get_latency, get_error, _ = request(base_url + f"/orders/{order_id}")
        metrics.record(get_latency, get_error)
        reserve_latency, reserve_error, _ = request(base_url + f"/orders/{order_id}/reserve", "POST")
        metrics.record(reserve_latency, reserve_error)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8080")
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--duration", type=int, default=30, help="fixed duration in seconds")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.concurrency < 1 or args.duration < 1:
        parser.error("--concurrency and --duration must be positive")

    metrics = Metrics()
    started = time.perf_counter()
    deadline = started + args.duration
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(worker, args.base_url.rstrip("/"), deadline, metrics, i) for i in range(args.concurrency)]
        for future in futures:
            future.result()
    elapsed = time.perf_counter() - started
    values = metrics.latencies_ms
    result = {
        "workload": {
            "concurrency": args.concurrency,
            "duration_seconds": args.duration,
            "requests": metrics.requests,
            "operations": ["POST /orders", "GET /orders/{id}", "POST /orders/{id}/reserve"],
        },
        "metrics": {
            "p50_latency_ms": round(percentile(values, 50), 2),
            "p95_latency_ms": round(percentile(values, 95), 2),
            "p99_latency_ms": round(percentile(values, 99), 2),
            "throughput_rps": round(metrics.requests / elapsed, 2) if elapsed else 0.0,
            "error_rate": round(metrics.errors / metrics.requests, 6) if metrics.requests else 1.0,
            "errors": metrics.errors,
        },
        "environment": {
            "base_url": args.base_url,
            "runner": "Python standard library ThreadPoolExecutor",
            "notes": "Local Docker Compose environment; record host CPU, memory, Docker, and database image separately.",
        },
    }
    print(json.dumps(result, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
