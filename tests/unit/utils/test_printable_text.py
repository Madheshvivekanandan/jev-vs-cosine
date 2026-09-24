from app.utils.printable_text import to_printable


def test_to_printable_leaves_plain_text_alone() -> None:
    assert to_printable("rate limited (retry later)") == "rate limited (retry later)"


def test_to_printable_escapes_newlines_and_escape_codes() -> None:
    assert to_printable("a\nb\x1b[0m") == "a\\nb\\x1b[0m"


def test_to_printable_caps_length() -> None:
    assert to_printable("x" * 10, max_length=4) == "xxxx…"
