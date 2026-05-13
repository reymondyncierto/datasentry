from pipeline.exceptions import BusinessRuleError, InvalidTypeError, MissingFieldError


def test_validation_subclasses_include_context() -> None:
    err = MissingFieldError(3, "transaction_id", "", "missing_required")

    assert err.row_index == 3
    assert err.field_name == "transaction_id"
    assert err.bad_value == ""
    assert err.reason == "missing_required"


def test_validation_error_str_is_contextual() -> None:
    err = InvalidTypeError(5, "amount", "abc", "invalid_type")

    assert "row=5" in str(err)
    assert "field=amount" in str(err)


def test_business_rule_error_is_validation_error() -> None:
    err = BusinessRuleError(9, "amount", -1, "must_be_positive")

    assert err.reason == "must_be_positive"
