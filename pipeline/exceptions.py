"""Custom exception hierarchy for DataSentry."""

from __future__ import annotations

from dataclasses import dataclass


class DataSentryError(Exception):
    """Base class for all DataSentry exceptions."""


@dataclass(slots=True)
class ValidationError(DataSentryError):
    row_index: int
    field_name: str
    bad_value: object
    reason: str

    def __str__(self) -> str:
        return (
            f"row={self.row_index} field={self.field_name} "
            f"value={self.bad_value!r} reason={self.reason}"
        )


class MissingFieldError(ValidationError):
    """Raised when a required field is missing."""


class InvalidTypeError(ValidationError):
    """Raised when a field type is invalid."""


class BusinessRuleError(ValidationError):
    """Raised when a value violates a business rule."""


class DatabaseWriteError(DataSentryError):
    """Raised when writing to SQLite fails."""


class FileReadError(DataSentryError):
    """Raised when the input CSV cannot be read safely."""
