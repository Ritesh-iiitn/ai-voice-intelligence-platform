import pytest
from scripts.evaluate_retrieval import evaluate_knowledge_base

def test_retrieval_benchmark_meets_accuracy_threshold():
    results, mrr, mean_p3 = evaluate_knowledge_base()
    assert len(results) >= 5
    assert mrr >= 0.80
    assert mean_p3 >= 0.50
    incorrect_count = sum(1 for r in results if r["verdict"] == "incorrect")
    assert incorrect_count == 0
