from evaluation.harness import run_evaluation_suite


def test_evaluation_scenarios_pass():
    results = run_evaluation_suite()
    assert results, "Expected evaluation scenarios to run"
    for result in results:
        assert result["passed"], f"Scenario {result['scenario']} failed checks: {result['checks']}"
        assert result["outfit_count"] >= 1
