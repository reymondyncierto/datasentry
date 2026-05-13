from generate_data import generate_rows


def test_clean_mode_generates_valid_count() -> None:
    rows = generate_rows("clean", 10, 0.2)
    assert len(rows) == 10


def test_corrupt_mode_injects_faults() -> None:
    rows = generate_rows("corrupt", 10, 0.2)
    assert any(row["status"] == "processing" or row["customer_id"] == "" for row in rows)


def test_corrupt_mode_every_row_is_corrupted() -> None:
    rows = generate_rows("corrupt", 18, 0.2)
    assert len(rows) == 18

    seen: set[str] = set()

    def is_corrupt(row: dict[str, object]) -> bool:
        amount = row["amount"]
        date_value = str(row["transaction_date"])
        tx_id = str(row["transaction_id"])
        is_duplicate = tx_id in seen
        seen.add(tx_id)
        return (
            row["customer_id"] == ""
            or (isinstance(amount, (int, float)) and amount < 0)
            or (isinstance(amount, str) and not amount.replace(".", "", 1).isdigit())
            or "/" in date_value
            or row["status"] == "processing"
            or is_duplicate
        )

    assert all(is_corrupt(row) for row in rows)
