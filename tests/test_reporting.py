from src.reporting import (
    build_executive_metrics,
    build_preference_value_view,
    build_priority_view,
    build_quality_view,
    build_stratum_view,
    load_report_data,
)


def test_executive_metrics_are_built_from_final_outputs():
    metrics = build_executive_metrics(load_report_data())

    assert metrics["customer_count"] == 3183
    assert round(metrics["estimated_period_spend"]) == 719624
    assert metrics["vegetarian_coverage_index"] == 1.42
    assert round(metrics["seafood_estimated_spend"]) == 178967


def test_reporting_views_keep_presentation_logic_out_of_notebook():
    report = load_report_data()

    assert len(build_stratum_view(report.customer_value)) == 4
    assert len(build_preference_value_view(report.preference_opportunity)) == 6
    assert "Otro" not in set(
        build_priority_view(report.preference_opportunity)["customer_preference"]
    )
    assert set(build_quality_view(report.data_quality).columns) == {
        "dataset",
        "step",
        "rows",
        "columns",
        "missing_total",
        "duplicate_rows",
    }
