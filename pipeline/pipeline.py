"""Pipeline orchestrator for CSV ingestion."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import uuid4

from pipeline.exceptions import DatabaseWriteError, FileReadError, ValidationError
from pipeline.loader import SQLiteLoader
from pipeline.logger import configure_logger
from pipeline.report import render_audit_report
from pipeline.transformer import transform_transaction
from pipeline.validators import validate_row


class PipelineResult(dict):
    pass


def run_pipeline(input_path: str, db_path: str, log_file: str | None = None) -> PipelineResult:
    run_id = str(uuid4())
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
                    loader.write_rejected_row(
                        run_id=run_id,
                        row_index=exc.row_index,
                        field_name=exc.field_name,
                        bad_value=exc.bad_value,
                        reason=exc.reason,
                        raw_row=json.dumps(row, ensure_ascii=True),
                    )
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
            "run_id": run_id,
            "report": summary,
        }
    )


def export_rejected_rows(db_path: str, run_id: str, output_path: str) -> int:
    loader = SQLiteLoader(db_path)
    loader.initialize()
    return loader.export_rejected_rows_to_csv(run_id=run_id, output_path=output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=False)

    run_parser = subparsers.add_parser("run", help="Run CSV ingestion pipeline")
    run_parser.add_argument("--input", required=True)
    run_parser.add_argument("--db", default="datasentry.db")
    run_parser.add_argument("--log-file", default=None)

    export_parser = subparsers.add_parser(
        "export-rejected",
        help="Export rejected rows for a run_id to CSV",
    )
    export_parser.add_argument("--db", default="datasentry.db")
    export_parser.add_argument("--run-id", required=True)
    export_parser.add_argument("--output", required=True)

    # Backward-compatible flags without explicit subcommand.
    parser.add_argument("--input")
    parser.add_argument("--db", default="datasentry.db")
    parser.add_argument("--log-file", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "export-rejected":
        exported = export_rejected_rows(args.db, args.run_id, args.output)
        print(f"exported_rejected_rows: {exported}")
        print(f"output_path: {args.output}")
        return

    input_path = getattr(args, "input", None)
    if not input_path:
        raise SystemExit("input is required (use `run --input` or `--input`).")

    result = run_pipeline(input_path, args.db, args.log_file)
    print(f"run_id: {result['run_id']}")
    print(result["report"])


if __name__ == "__main__":
    main()
