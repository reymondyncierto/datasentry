"""Pipeline orchestrator for CSV ingestion."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path
from typing import Any

from pipeline.exceptions import DatabaseWriteError, FileReadError, ValidationError
from pipeline.loader import SQLiteLoader
from pipeline.logger import configure_logger
from pipeline.report import render_audit_report
from pipeline.transformer import transform_transaction
from pipeline.validators import validate_row


class PipelineResult(dict):
    pass


def run_pipeline(input_path: str, db_path: str, log_file: str | None = None) -> PipelineResult:
    logger = configure_logger(file_path=log_file)
    loader = SQLiteLoader(db_path)
    loader.initialize()

    processed = 0
    succeeded = 0
    failed = 0
    failure_reasons: Counter[str] = Counter()

    csv_file = Path(input_path)
    if not csv_file.exists():
        logger.critical("input file missing")
        raise FileReadError(f"missing file: {input_path}")

    try:
        with csv_file.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {
                "transaction_id",
                "customer_id",
                "amount",
                "currency",
                "transaction_date",
                "status",
                "description",
            }
            if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
                raise FileReadError("missing required CSV headers")

            for row_index, row in enumerate(reader, start=1):
                processed += 1
                try:
                    validated = validate_row(row, row_index)
                    transformed = transform_transaction(validated)
                    loader.write(transformed, row_index=row_index)
                    succeeded += 1
                except ValidationError as exc:
                    failed += 1
                    failure_reasons[exc.reason] += 1
                    logger.warning(
                        "row skipped",
                        extra={
                            "row_index": exc.row_index,
                            "field_name": exc.field_name,
                            "bad_value": exc.bad_value,
                            "reason": exc.reason,
                        },
                    )
                except DatabaseWriteError:
                    logger.error("database write failure")
                    raise
    except UnicodeDecodeError as exc:
        logger.critical("input file not utf-8")
        raise FileReadError("input CSV is not valid UTF-8") from exc
    except OSError as exc:
        logger.critical("input file cannot be opened")
        raise FileReadError(f"input CSV could not be opened: {input_path}") from exc

    summary = render_audit_report(processed, succeeded, failed, failure_reasons)
    logger.info("run complete")
    return PipelineResult(
        {
            "rows_processed": processed,
            "rows_written": succeeded,
            "rows_failed": failed,
            "failure_breakdown": dict(failure_reasons),
            "report": summary,
        }
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--db", default="datasentry.db")
    parser.add_argument("--log-file", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_pipeline(args.input, args.db, args.log_file)
    print(result["report"])


if __name__ == "__main__":
    main()
