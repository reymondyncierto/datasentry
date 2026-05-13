from uuid import uuid4

import pytest

from pipeline.exceptions import BusinessRuleError, InvalidTypeError, MissingFieldError
from pipeline.validators import validate_row


def make_row() -> dict[str, object]:
    return {
        "transaction_id": str(uuid4()),
        "customer_id": "CUST100",
        "amount": 12.5,
        "currency": "USD",
        "transaction_date": "2026-05-13",
        "status": "completed",
        "description": "ok",
    }


def test_valid_row_passes() -> None:
    tx = validate_row(make_row(), 1)

    assert tx.amount == 12.5


def test_missing_required_field() -> None:
    row = make_row()
    row.pop("transaction_id")

    with pytest.raises(MissingFieldError):
        validate_row(row, 2)


def test_negative_amount_rejected() -> None:
    row = make_row()
    row["amount"] = -50.0

    with pytest.raises(BusinessRuleError):
        validate_row(row, 3)


def test_non_numeric_amount() -> None:
    row = make_row()
    row["amount"] = "abc"

    with pytest.raises(InvalidTypeError):
        validate_row(row, 4)
