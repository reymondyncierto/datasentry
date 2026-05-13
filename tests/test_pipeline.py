import csv
from pathlib import Path

import pytest

from pipeline.exceptions import DatabaseWriteError, FileReadError
from pipeline.loader import SQLiteLoader
from pipeline.pipeline import run_pipeline


HEADERS = [
    "transaction_id",
    "customer_id",
    "amount",
    "currency",
    "transaction_date",
    "status",
    "description",
]


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def test_partial_bad_rows_are_skipped(tmp_path: Path) -> None:
    csv_path = tmp_path / "input.csv"
    db_path = tmp_path / "test.db"

    rows = [
        {
            "transaction_id": "8d8b6f03-5a5a-4fd6-bcf1-9a6f10862ef0",
            "customer_id": "CUST1",
            "amount": "10.50",
            "currency": "usd",
            "transaction_date": "2026-05-13",
            "status": "completed",
            "description": "ok",
        },
        {
            "transaction_id": "1c571f7f-b9b3-4054-94f6-e31680e2bae2",
            "customer_id": "",
            "amount": "10.50",
            "currency": "usd",
            "transaction_date": "2026-05-13",
            "status": "completed",
            "description": "bad",
        },
    ]
    write_rows(csv_path, rows)

    result = run_pipeline(str(csv_path), str(db_path))

    assert result["rows_processed"] == 2
    assert result["rows_written"] == 1
    assert result["rows_failed"] == 1


def test_empty_csv_file(tmp_path: Path) -> None:
    csv_path = tmp_path / "input.csv"
    db_path = tmp_path / "test.db"

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()

    result = run_pipeline(str(csv_path), str(db_path))

    assert result["rows_processed"] == 0
    assert result["rows_written"] == 0


def test_missing_header_raises_file_read_error(tmp_path: Path) -> None:
    csv_path = tmp_path / "input.csv"
    db_path = tmp_path / "test.db"

    csv_path.write_text("transaction_id,customer_id\n1,a\n", encoding="utf-8")

    with pytest.raises(FileReadError):
        run_pipeline(str(csv_path), str(db_path))


def test_db_write_failure_halts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    csv_path = tmp_path / "input.csv"
    db_path = tmp_path / "test.db"

    write_rows(
        csv_path,
        [
            {
                "transaction_id": "8d8b6f03-5a5a-4fd6-bcf1-9a6f10862ef0",
                "customer_id": "CUST1",
                "amount": "10.50",
                "currency": "usd",
                "transaction_date": "2026-05-13",
                "status": "completed",
                "description": "ok",
            }
        ],
    )

    def _boom(self: SQLiteLoader, row: dict[str, str]) -> None:  # pragma: no cover
        raise DatabaseWriteError("forced failure")

    monkeypatch.setattr(SQLiteLoader, "write", _boom)

    with pytest.raises(DatabaseWriteError):
        run_pipeline(str(csv_path), str(db_path))


def test_audit_report_accuracy(tmp_path: Path) -> None:
    csv_path = tmp_path / "input.csv"
    db_path = tmp_path / "test.db"

    rows = []
    for i in range(10):
        rows.append(
            {
                "transaction_id": f"8d8b6f03-5a5a-4fd6-bcf1-9a6f10862ef{i}",
                "customer_id": "CUST1" if i < 7 else "",
                "amount": "10.50",
                "currency": "usd",
                "transaction_date": "2026-05-13",
                "status": "completed",
                "description": "ok",
            }
        )

    write_rows(csv_path, rows)
    result = run_pipeline(str(csv_path), str(db_path))

    assert result["rows_processed"] == 10
    assert result["rows_written"] == 7
    assert result["rows_failed"] == 3
