import pytest
from scripts.evaluate_multilingual import run_multilingual_evaluation, EVAL_CASES

def test_multilingual_evaluation_benchmark():
    assert len(EVAL_CASES) == 10
    # Run benchmark to verify no errors
    run_multilingual_evaluation()
