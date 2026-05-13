"""SQLite loading layer for DataSentry."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from pipeline.exceptions import DatabaseWriteError


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
            conn.commit()
        except sqlite3.Error as exc:
            raise DatabaseWriteError(str(exc)) from exc
        finally:
            conn.close()

    def write(self, row: dict[str, Any]) -> None:
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
