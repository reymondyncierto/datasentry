"""Centralized structured logging setup."""

from __future__ import annotations

import logging
from pathlib import Path

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | row=%(row_index)s "
    "field=%(field_name)s value=%(bad_value)s reason=%(reason)s"
)


class ContextDefaultsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for key in ("row_index", "field_name", "bad_value", "reason"):
            if not hasattr(record, key):
                setattr(record, key, "-")
        return True


def configure_logger(level: str = "INFO", file_path: str | None = None) -> logging.Logger:
    logger = logging.getLogger("datasentry")
    logger.setLevel(level.upper())
    logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)
    context_filter = ContextDefaultsFilter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(context_filter)
    logger.addHandler(stream_handler)

    if file_path:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        logger.addHandler(file_handler)

    return logger
