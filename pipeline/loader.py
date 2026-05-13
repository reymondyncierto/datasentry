"""SQLite loading layer for DataSentry."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.exceptions import DatabaseWriteError, DuplicateTransactionError


class SQLiteLoader:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def initialize(self) -> None:
        try:
            conn = self._connect()
        except sqlite3.Error as exc:
            raise DatabaseWriteError(str(exc)) from exc
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    description TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS rejected_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    row_index INTEGER NOT NULL,
                    field_name TEXT NOT NULL,
                    bad_value TEXT,
                    reason TEXT NOT NULL,
                    raw_row TEXT NOT NULL,
                    rejected_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseWriteError(str(exc)) from exc
        finally:
            conn.close()

    def write(self, row: dict[str, Any], row_index: int) -> None:
        try:
            conn = self._connect()
        except sqlite3.Error as exc:
            raise DatabaseWriteError(str(exc)) from exc
        try:
            conn.execute(
                """
                INSERT INTO transactions (
                    transaction_id,
                    customer_id,
                    amount,
                    currency,
                    transaction_date,
                    status,
                    description
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["transaction_id"],
                    row["customer_id"],
                    row["amount"],
                    row["currency"],
                    row["transaction_date"],
                    row["status"],
                    row["description"],
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed: transactions.transaction_id" in str(exc):
                raise DuplicateTransactionError(
                    row_index=row_index,
                    field_name="transaction_id",
                    bad_value=row["transaction_id"],
                    reason="duplicate_transaction_id",
                ) from exc
            raise DatabaseWriteError(str(exc)) from exc
        except sqlite3.Error as exc:
            raise DatabaseWriteError(str(exc)) from exc
        finally:
            conn.close()

    def count_rows(self) -> int:
        if not Path(self.db_path).exists():
            return 0
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()
            return int(row[0])
        finally:
            conn.close()

    def count_rejected_rows(self) -> int:
        if not Path(self.db_path).exists():
            return 0
        conn = self._connect()
        try:
            row = conn.execute("SELECT COUNT(*) FROM rejected_transactions").fetchone()
            return int(row[0])
        finally:
            conn.close()

    def write_rejected_row(
        self,
        run_id: str,
        row_index: int,
        field_name: str,
        bad_value: object,
        reason: str,
        raw_row: str,
    ) -> None:
        try:
            conn = self._connect()
        except sqlite3.Error as exc:
            raise DatabaseWriteError(str(exc)) from exc
        try:
            conn.execute(
                """
                INSERT INTO rejected_transactions (
                    run_id,
                    row_index,
                    field_name,
                    bad_value,
                    reason,
                    raw_row,
                    rejected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    row_index,
                    field_name,
                    str(bad_value) if bad_value is not None else None,
                    reason,
                    raw_row,
                    datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                ),
            )
            conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseWriteError(str(exc)) from exc
        finally:
            conn.close()
