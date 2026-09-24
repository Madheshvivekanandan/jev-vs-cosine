import json
from pathlib import Path

import pytest

from app.domain.errors.configuration_error import ConfigurationError
from app.repositories.reference_case_repository import load_reference_cases

_SHIPPED = Path(__file__).resolve().parents[3] / "fingerprints" / "typesafe_reference.v1.json"


def test_load_reference_cases_reads_the_shipped_file() -> None:
    cases = load_reference_cases(_SHIPPED)

    assert [c.case_id for c in cases][:2] == ["opencode_recording_bridge", "typesafe_quickstart"]
    assert cases[0].reference_response["usage"] == {"input_tokens": 422, "output_tokens": 69}
    assert len(cases) == 6


@pytest.mark.parametrize("content", ["[]", "[{}]", "not json"])
def test_load_reference_cases_rejects_bad_files(tmp_path: Path, content: str) -> None:
    path = tmp_path / "cases.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_reference_cases(path)


def test_load_reference_cases_when_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="not found"):
        load_reference_cases(tmp_path / "absent.json")


def test_load_reference_cases_keeps_the_request_verbatim(tmp_path: Path) -> None:
    case = {
        "id": "c",
        "source_url": "u",
        "reference_model": "jev-1.13.0",
        "request": {"state": {"a": [1, 2]}, "questions": {"q": {"type": "noul"}}},
        "reference_response": {"answers": {}},
    }
    path = tmp_path / "cases.json"
    path.write_text(json.dumps([case]), encoding="utf-8")

    loaded = load_reference_cases(path)[0]

    assert loaded.state == {"a": [1, 2]}
    assert loaded.questions == {"q": {"type": "noul"}}
