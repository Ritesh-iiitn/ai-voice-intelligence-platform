#!/usr/bin/env python3
"""Unified runner executing Q4 Real-Time Latency Benchmark and False Positive Evaluation."""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from q4_realtime.evaluation.benchmark import RealTimeLatencyBenchmark
from q4_realtime.evaluation.eval_fp import SignalFPEvaluator


async def main():
    print("=" * 70)
    print("🚀 Running Q4 Real-Time Streaming & Signal Detection Evaluations")
    print("=" * 70)

    # 1. Run Latency Benchmark
    print("\n[Stage 1/2] Benchmarking Real-Time Sub-Second Latency (100 sequential chunks)...")
    bench = RealTimeLatencyBenchmark(iterations=100)
    latency_res = await bench.run_benchmark()
    latency_report_path = "docs/latency/Q4_LATENCY_REPORT.md"
    bench.generate_report(latency_res, latency_report_path)

    e2e_p95 = latency_res["Total Pipeline E2E"]["p95"]
    print(f"  ✓ Stage 1 Complete: Total E2E P95 = {e2e_p95}ms (< 1000ms SLA)")

    # 2. Run False Positive / Accuracy Evaluation
    print("\n[Stage 2/2] Evaluating Signal Detection Precision, Recall & False Positives (18 cases)...")
    fp_eval = SignalFPEvaluator()
    fp_res = await fp_eval.evaluate()
    fp_report_path = "docs/evaluation/q4_false_positive_results.md"
    fp_eval.generate_report(fp_res, fp_report_path)

    overall_prec = fp_res["metrics"]["overall"]["precision"] * 100
    overall_rec = fp_res["metrics"]["overall"]["recall"] * 100
    overall_fp = fp_res["metrics"]["overall"]["fp_rate"] * 100
    print(f"  ✓ Stage 2 Complete: Precision={overall_prec:.1f}%, Recall={overall_rec:.1f}%, FP Rate={overall_fp:.1f}%")

    print("\n" + "=" * 70)
    print(f"✅ All evaluations finished successfully!")
    print(f"   • Latency report: {latency_report_path}")
    print(f"   • False-positive report: {fp_report_path}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
