"""Row validation and error mapping helpers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError as PydanticValidationError

from pipeline.exceptions import BusinessRuleError, InvalidTypeError, MissingFieldError
from pipeline.models import Transaction

BUSINESS_MESSAGES = {
    "must_be_positive",
    "must_be_uuid_v4",
    "must_be_alphanumeric",
    "must_be_iso_4217",
}


def validate_row(row: Mapping[str, Any], row_index: int) -> Transaction:
    try:
        return Transaction.model_validate(dict(row))
    except PydanticValidationError as exc:
        first_error = exc.errors()[0]
        loc = first_error.get("loc", ["unknown"])
        field_name = str(loc[0]) if loc else "unknown"
        bad_value = row.get(field_name)
        err_type = first_error.get("type", "")
        reason = first_error.get("msg", "validation_failed")

        if err_type == "missing":
            raise MissingFieldError(row_index, field_name, bad_value, "missing_required") from exc

        if any(token in err_type for token in ("parsing", "type")):
            raise InvalidTypeError(row_index, field_name, bad_value, reason) from exc

        for marker in BUSINESS_MESSAGES:
            if marker in reason:
                raise BusinessRuleError(row_index, field_name, bad_value, marker) from exc

        if "Input should be 'pending', 'completed' or 'failed'" in reason:
            raise BusinessRuleError(row_index, field_name, bad_value, "invalid_status") from exc

        raise InvalidTypeError(row_index, field_name, bad_value, reason) from exc
