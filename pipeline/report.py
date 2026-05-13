"""Audit report rendering."""

from __future__ import annotations

from collections import Counter


def render_audit_report(
    processed: int,
    success: int,
    failed: int,
    failure_reasons: Counter[str],
) -> str:
    lines = [
        "DataSentry Audit Report",
        f"rows_processed: {processed}",
        f"rows_written: {success}",
        f"rows_failed: {failed}",
        "failure_breakdown:",
    ]

    if not failure_reasons:
        lines.append("  - none")
    else:
        for reason, count in sorted(failure_reasons.items()):
            lines.append(f"  - {reason}: {count}")

    return "\n".join(lines)
