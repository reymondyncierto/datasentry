from collections import Counter

from pipeline.report import render_audit_report


def test_report_contains_required_counts() -> None:
    report = render_audit_report(10, 7, 3, Counter({"invalid_type": 2, "missing_required": 1}))

    assert "rows_processed: 10" in report
    assert "rows_written: 7" in report
    assert "rows_failed: 3" in report
    assert "invalid_type: 2" in report
