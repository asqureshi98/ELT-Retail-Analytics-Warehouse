from scripts.warehouse_quality_checks import (
    CheckSpec,
    evaluate_check,
    summarize_results,
)


def test_evaluate_check_passes_when_metric_is_inside_bounds():
    spec = CheckSpec(
        name="marts_non_empty",
        description="fact sales has rows",
        sql="select count(*) from marts.fct_sales",
        metric_key="row_count",
        min_value=1,
    )

    result = evaluate_check(spec, {"row_count": 10})

    assert result.passed is True
    assert result.observed_value == 10
    assert result.status == "pass"
    assert result.details["min_value"] == 1


def test_evaluate_check_fails_when_metric_is_outside_bounds():
    spec = CheckSpec(
        name="refund_sanity",
        description="refunds cannot exceed sales revenue",
        sql="select 125.0 as refund_pct",
        metric_key="refund_pct",
        max_value=100,
    )

    result = evaluate_check(spec, {"refund_pct": 125.0})

    assert result.passed is False
    assert result.status == "fail"
    assert "<= 100" in result.message


def test_evaluate_check_fails_when_metric_is_missing():
    spec = CheckSpec(
        name="missing_metric",
        description="metric must be present",
        sql="select 1",
        metric_key="missing_count",
        equals=0,
    )

    result = evaluate_check(spec, {"other_count": 0})

    assert result.passed is False
    assert result.status == "fail"
    assert "missing_count" in result.message


def test_evaluate_check_fails_when_metric_is_null():
    spec = CheckSpec(
        name="null_metric",
        description="metric must have a value",
        sql="select null as row_count",
        metric_key="row_count",
        min_value=1,
    )

    result = evaluate_check(spec, {"row_count": None})

    assert result.passed is False
    assert result.status == "fail"
    assert "null" in result.message.lower()


def test_summarize_results_counts_pass_fail_and_sets_exit_code():
    passing = evaluate_check(
        CheckSpec("passing", "passes", "select 0", "bad_rows", equals=0),
        {"bad_rows": 0},
    )
    failing = evaluate_check(
        CheckSpec("failing", "fails", "select 2", "bad_rows", equals=0),
        {"bad_rows": 2},
    )

    summary = summarize_results([passing, failing])

    assert summary["status"] == "fail"
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["total"] == 2
    assert summary["exit_code"] == 1
    assert [check["name"] for check in summary["checks"]] == ["passing", "failing"]
