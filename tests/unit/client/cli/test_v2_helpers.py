from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel

from ai.backend.client.cli.v2.helpers import load_model, run_async
from ai.backend.client.exceptions import BackendAPIError


class _Entry(BaseModel):
    name: str
    count: int


class TestLoadModel:
    """Tests for the ``load_model`` JSON/``@file`` loader."""

    def test_raw_json_single_model(self) -> None:
        result = load_model('{"name": "a", "count": 1}', _Entry)

        assert result == _Entry(name="a", count=1)

    def test_raw_json_list(self) -> None:
        result = load_model('[{"name": "a", "count": 1}, {"name": "b", "count": 2}]', list[_Entry])

        assert result == [_Entry(name="a", count=1), _Entry(name="b", count=2)]

    def test_raw_json_empty_list(self) -> None:
        result = load_model("[]", list[_Entry])

        assert result == []

    def test_file_payload(self, tmp_path: Path) -> None:
        path = tmp_path / "entries.json"
        path.write_text('[{"name": "a", "count": 1}]')

        result = load_model(f"@{path}", list[_Entry])

        assert result == [_Entry(name="a", count=1)]

    def test_invalid_json_exits(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            load_model("[{bad", list[_Entry])

        assert exc_info.value.code == 1

    def test_validation_error_exits(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            load_model('[{"name": "a", "count": "not-an-int"}]', list[_Entry])

        assert exc_info.value.code == 1

    def test_missing_file_exits(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            load_model("@/tmp/role_preset_does_not_exist.json", list[_Entry])

        assert exc_info.value.code == 1


class TestRunAsync:
    """Tests for the ``run_async`` coroutine runner."""

    def test_success_runs_coroutine(self) -> None:
        ran = []

        async def _coro() -> None:
            ran.append(True)

        run_async(_coro)

        assert ran == [True]

    def test_api_error_exits_with_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        async def _coro() -> None:
            raise BackendAPIError(404, "Not Found", {"title": "No such role_preset."})

        with pytest.raises(SystemExit) as exc_info:
            run_async(_coro)

        assert exc_info.value.code == 1
        assert "No such role_preset." in capsys.readouterr().err
