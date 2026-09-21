"""Unit test running the Q4 real-time benchmark and evaluation suite."""

import pytest
from q4_realtime.evaluation.benchmark import RealTimeLatencyBenchmark
from q4_realtime.evaluation.eval_fp import SignalFPEvaluator


@pytest.mark.asyncio
async def test_realtime_latency_benchmark_passes_sla():
    bench = RealTimeLatencyBenchmark(iterations=10)
    results = await bench.run_benchmark()

    # Verify E2E P95 latency is well below 1000ms SLA
    e2e_p95 = results["Total Pipeline E2E"]["p95"]
    assert e2e_p95 < 1000.0
    assert results["Signal Detection"]["mean"] < 100.0
    assert results["Nudge Engine"]["mean"] < 50.0


@pytest.mark.asyncio
async def test_signal_fp_evaluator_high_accuracy():
    evaluator = SignalFPEvaluator()
    res = await evaluator.evaluate()

    metrics = res["metrics"]["overall"]
    assert metrics["precision"] >= 0.90
    assert metrics["recall"] >= 0.90
    assert metrics["fp_rate"] <= 0.05
