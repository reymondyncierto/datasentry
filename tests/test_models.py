from uuid import uuid4

import pytest
from pydantic import ValidationError

from pipeline.models import Transaction


def make_row() -> dict[str, object]:
    return {
        "transaction_id": str(uuid4()),
        "customer_id": "CUST100",
        "amount": 12.5,
        "currency": "usd",
        "transaction_date": "2026-05-13",
        "status": "completed",
        "description": "ok",
    }


def test_valid_model_passes() -> None:
    tx = Transaction.model_validate(make_row())

    assert tx.currency == "USD"


def test_negative_amount_rejected() -> None:
    row = make_row()
    row["amount"] = -1.0

    with pytest.raises(ValidationError):
        Transaction.model_validate(row)


def test_invalid_status_rejected() -> None:
    row = make_row()
    row["status"] = "processing"

    with pytest.raises(ValidationError):
        Transaction.model_validate(row)


def test_invalid_date_format_rejected() -> None:
    row = make_row()
    row["transaction_date"] = "13-05-2026"

    with pytest.raises(ValidationError):
        Transaction.model_validate(row)
