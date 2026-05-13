"""Pydantic models for pipeline records."""

from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    transaction_id: UUID
    customer_id: str = Field(min_length=1)
    amount: float
    currency: str
    transaction_date: date
    status: Literal["pending", "completed", "failed"]
    description: str | None = Field(default=None, max_length=255)

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id_v4(cls, value: UUID) -> UUID:
        if value.version != 4:
            raise ValueError("must_be_uuid_v4")
        return value

    @field_validator("customer_id")
    @classmethod
    def validate_customer_id(cls, value: str) -> str:
        if not value.isalnum():
            raise ValueError("must_be_alphanumeric")
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("must_be_positive")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        normalized = value.upper()
        if len(normalized) != 3 or not normalized.isalpha():
            raise ValueError("must_be_iso_4217")
        return normalized
