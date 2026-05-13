from uuid import uuid4

from pipeline.models import Transaction
from pipeline.transformer import transform_transaction


def test_transform_normalizes_currency_and_whitespace() -> None:
    tx = Transaction.model_validate(
        {
            "transaction_id": str(uuid4()),
            "customer_id": "CUST100 ",
            "amount": 20.0,
            "currency": "usd",
            "transaction_date": "2026-05-13",
            "status": "pending",
            "description": "  hello  ",
        }
    )

    out = transform_transaction(tx)

    assert out["currency"] == "USD"
    assert out["customer_id"] == "CUST100"
    assert out["description"] == "hello"
