"""Synthetic CSV generator for DataSentry."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from typing import Any
from uuid import uuid4

from faker import Faker

faker = Faker()

FAULT_TYPES = (
    "null_required_field",
    "negative_amount",
    "bad_date_format",
    "invalid_status",
    "wrong_type_amount",
    "duplicate_id",
)

HEADERS = [
    "transaction_id",
    "customer_id",
    "amount",
    "currency",
    "transaction_date",
    "status",
    "description",
]


def build_valid_row() -> dict[str, Any]:
    return {
        "transaction_id": str(uuid4()),
        "customer_id": faker.bothify(text="CUST####"),
        "amount": round(random.uniform(1.0, 2500.0), 2),
        "currency": random.choice(["USD", "EUR", "GBP"]),
        "transaction_date": faker.date(pattern="%Y-%m-%d"),
        "status": random.choice(["pending", "completed", "failed"]),
        "description": faker.sentence(nb_words=6)[:255],
    }


def apply_fault(row: dict[str, Any], fault: str, seen_ids: list[str]) -> dict[str, Any]:
    broken = dict(row)
    if fault == "null_required_field":
        broken["customer_id"] = ""
    elif fault == "negative_amount":
        broken["amount"] = -abs(float(broken["amount"]))
    elif fault == "bad_date_format":
        yyyy, mm, dd = str(broken["transaction_date"]).split("-")
        broken["transaction_date"] = f"{dd}/{mm}/{yyyy}"
    elif fault == "invalid_status":
        broken["status"] = "processing"
    elif fault == "wrong_type_amount":
        broken["amount"] = faker.lexify(text="????")
    elif fault == "duplicate_id" and seen_ids:
        broken["transaction_id"] = random.choice(seen_ids)
    return broken


def generate_rows(mode: str, rows: int, corrupt_ratio: float) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen_ids: list[str] = []
    for i in range(rows):
        base = build_valid_row()
        seen_ids.append(base["transaction_id"])

        if mode == "clean":
            output.append(base)
            continue

        if mode == "corrupt":
            output.append(apply_fault(base, FAULT_TYPES[i % len(FAULT_TYPES)], seen_ids))
            continue

        use_fault = random.random() < corrupt_ratio
        if use_fault:
            output.append(apply_fault(base, random.choice(FAULT_TYPES), seen_ids))
        else:
            output.append(base)
    return output


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["clean", "corrupt", "mixed"], default="mixed")
    parser.add_argument("--rows", type=int, default=100)
    parser.add_argument("--corrupt-ratio", type=float, default=0.2)
    parser.add_argument("--output", default="data/generated.csv")
    parser.add_argument("--seed", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.seed is not None:
        random.seed(args.seed)
        Faker.seed(args.seed)

    rows = generate_rows(args.mode, args.rows, args.corrupt_ratio)
    write_csv(Path(args.output), rows)


if __name__ == "__main__":
    main()
