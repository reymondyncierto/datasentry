# DataSentry

Resilient CSV ingestion pipeline (EVTL): Extract -> Validate -> Transform -> Load with audit reporting.

## Requirements
- Python 3.11+

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generate Data
```bash
python generate_data.py --mode clean --rows 100 --output data/clean.csv
python generate_data.py --mode corrupt --rows 100 --output data/corrupt.csv
python generate_data.py --mode mixed --rows 100 --corrupt-ratio 0.2 --output data/mixed.csv
```

Modes:
- `clean`: all valid rows
- `corrupt`: all rows intentionally corrupted
- `mixed`: valid/corrupt blend (default 80/20)

## Run Pipeline
```bash
python -m pipeline.pipeline run --input data/mixed.csv --db datasentry.db
```

Behavior:
- Validation failures are logged with `row`, `field`, `value`, and `reason`, then skipped.
- Skipped rows are persisted into `rejected_transactions` with a per-run `run_id`.
- DB write failures raise `DatabaseWriteError` and stop execution.
- File read/header issues raise `FileReadError` and stop execution.

## Audit Report
Run output includes:
- run_id
- rows processed
- rows written
- rows failed
- failure breakdown by reason

Example output:
```text
run_id: 4a9b25fb-7333-4b28-ac4d-c9b094fd628f
DataSentry Audit Report
rows_processed: 100
rows_written: 80
rows_failed: 20
failure_breakdown:
  - invalid_status: 5
  - duplicate_transaction_id: 4
  - ...
```

## Export Rejected Rows
Export all rejected rows for a specific run to CSV:

```bash
python -m pipeline.pipeline export-rejected \
  --db datasentry.db \
  --run-id 4a9b25fb-7333-4b28-ac4d-c9b094fd628f \
  --output data/rejected-4a9b25fb.csv
```

This CSV includes:
- `run_id`
- `row_index`
- `field_name`
- `bad_value`
- `reason`
- `raw_row`
- `rejected_at`

## Run Tests
```bash
pytest -q
```

## Implementation Map: Error Handling and Validation

### Proper Error Handling (intentional failure handling, no silent suppression)
- `pipeline/exceptions.py`: typed exception hierarchy for recoverable vs fatal paths (`ValidationError` subclasses, `DatabaseWriteError`, `FileReadError`).
- `pipeline/pipeline.py`: explicit error policy in orchestration.
  - Catches `ValidationError` per row, logs warning context, persists rejected row, continues.
  - Raises fatal `DatabaseWriteError` on non-recoverable DB faults.
  - Maps file open/encoding/header faults to `FileReadError`.
- `pipeline/loader.py`: DB-layer failure mapping.
  - Converts duplicate transaction key writes to `DuplicateTransactionError` (recoverable row rejection).
  - Keeps other SQLite faults as `DatabaseWriteError` (fatal).
- `pipeline/logger.py`: structured warning/error/critical logging with row context fields.
- Tests validating failure behavior:
  - `tests/test_pipeline.py`
  - `tests/test_loader.py`
  - `tests/test_exceptions.py`

### Proper Validation (input/schema/business-rule validation)
- `pipeline/models.py`: strict Pydantic transaction schema and business rules (UUID v4, positive amount, ISO date parsing, status enum, field constraints).
- `pipeline/validators.py`: row-validation adapter that maps schema/rule failures into typed validation errors with row/field/value/reason.
- `pipeline/transformer.py`: deterministic normalization before persistence (e.g., currency casing, whitespace handling).
- `generate_data.py`: controlled corruption modes for validation-path testing (`clean`, `corrupt`, `mixed`).
- Tests validating input/data correctness rules:
  - `tests/test_models.py`
  - `tests/test_validators.py`
  - `tests/test_transformer.py`
  - `tests/test_generate_data.py`
