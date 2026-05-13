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
python -m pipeline.pipeline --input data/mixed.csv --db datasentry.db
```

Behavior:
- Validation failures are logged with `row`, `field`, `value`, and `reason`, then skipped.
- DB write failures raise `DatabaseWriteError` and stop execution.
- File read/header issues raise `FileReadError` and stop execution.

## Audit Report
Run output includes:
- rows processed
- rows written
- rows failed
- failure breakdown by reason

## Run Tests
```bash
pytest -q
```
