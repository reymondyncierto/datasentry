import sqlite3
from pathlib import Path

import pytest

from pipeline.exceptions import DatabaseWriteError, DuplicateTransactionError
from pipeline.loader import SQLiteLoader


def sample_row() -> dict[str, object]:
    return {
        "transaction_id": "a7fd2000-1111-4d3b-bb55-a2f3d111aaa1",
        "customer_id": "CUST100",
        "amount": 10.0,
        "currency": "USD",
        "transaction_date": "2026-05-13",
        "status": "completed",
        "description": "hello",
    }


def test_loader_writes_row(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    loader = SQLiteLoader(str(db_path))

    loader.initialize()
    loader.write(sample_row(), row_index=1)

    assert loader.count_rows() == 1


def test_loader_db_failure_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = tmp_path / "test.db"
    loader = SQLiteLoader(str(db_path))

    def _boom() -> sqlite3.Connection:
        raise sqlite3.OperationalError("db down")

    monkeypatch.setattr(loader, "_connect", _boom)

    with pytest.raises(DatabaseWriteError):
        loader.initialize()


def test_loader_duplicate_id_raises_typed_error(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    loader = SQLiteLoader(str(db_path))
    row = sample_row()

    loader.initialize()
    loader.write(row, row_index=1)

    with pytest.raises(DuplicateTransactionError):
        loader.write(row, row_index=2)


def test_loader_persists_rejected_row(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    loader = SQLiteLoader(str(db_path))
    loader.initialize()

    loader.write_rejected_row(
        run_id="run-1",
        row_index=5,
        field_name="amount",
        bad_value="abc",
        reason="invalid_type",
        raw_row='{"amount":"abc"}',
    )

    assert loader.count_rejected_rows() == 1
