from pipeline.logger import LOG_FORMAT, configure_logger


def test_logger_configures_datasentry_logger() -> None:
    logger = configure_logger(level="DEBUG")

    assert logger.name == "datasentry"
    assert logger.level == 10


def test_log_format_contains_context_keys() -> None:
    assert "row=%(row_index)s" in LOG_FORMAT
    assert "field=%(field_name)s" in LOG_FORMAT
