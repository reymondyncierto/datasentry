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
