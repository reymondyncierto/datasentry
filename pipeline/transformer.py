"""Transformation helpers for normalized transaction output."""

from __future__ import annotations

from pipeline.models import Transaction


def transform_transaction(transaction: Transaction) -> dict[str, object]:
    return {
        "transaction_id": str(transaction.transaction_id),
        "customer_id": transaction.customer_id.strip(),
        "amount": transaction.amount,
        "currency": transaction.currency.upper(),
        "transaction_date": transaction.transaction_date.isoformat(),
        "status": transaction.status,
        "description": transaction.description.strip() if transaction.description else None,
    }
