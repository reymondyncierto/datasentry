from generate_data import generate_rows


def test_clean_mode_generates_valid_count() -> None:
    rows = generate_rows("clean", 10, 0.2)
    assert len(rows) == 10


def test_corrupt_mode_injects_faults() -> None:
    rows = generate_rows("corrupt", 10, 0.2)
    assert any(row["status"] == "processing" or row["amount"] == "" or row["customer_id"] == "" for row in rows)
