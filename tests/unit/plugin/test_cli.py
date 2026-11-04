import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pytest
from click.testing import CliRunner

from ai.backend.plugin.cli import main

_PLANTED_GROUP = "backendai_planted_v1"
_WHEELHOUSE_ROW = {"source": "wheelhouse", "name": "planted", "module_path": "planted"}


@dataclass(frozen=True)
class _ConfigFileCase:
    file_name: str


@pytest.fixture
def wheelhouse_with_planted_wheel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(sys, "path", [*sys.path])
    monkeypatch.delenv("BACKEND_CONFIG_FILE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    wheelhouse_path = tmp_path / "wheels"
    wheelhouse_path.mkdir()
    with zipfile.ZipFile(wheelhouse_path / "planted-1.0-py3-none-any.whl", "w") as wheel:
        wheel.writestr("planted.py", "")
        wheel.writestr(
            "planted-1.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: planted\nVersion: 1.0\n",
        )
        wheel.writestr(
            "planted-1.0.dist-info/entry_points.txt",
            f"[{_PLANTED_GROUP}]\nplanted = planted:Plugin\n",
        )
    return wheelhouse_path


@pytest.fixture
def daemon_config_allowing_the_wheelhouse(
    case: _ConfigFileCase, wheelhouse_with_planted_wheel: Path
) -> None:
    Path(case.file_name).write_text(
        f'[wheelhouse]\nallow = true\npath = "{wheelhouse_with_planted_wheel}"\n'
    )


@pytest.fixture
def named_config_allowing_the_wheelhouse(wheelhouse_with_planted_wheel: Path) -> Path:
    config_path = wheelhouse_with_planted_wheel.parent / "named.toml"
    config_path.write_text(
        f'[wheelhouse]\nallow = true\npath = "{wheelhouse_with_planted_wheel}"\n'
    )
    return config_path


@pytest.fixture
def named_config_not_allowing_the_wheelhouse(wheelhouse_with_planted_wheel: Path) -> Path:
    config_path = wheelhouse_with_planted_wheel.parent / "named.toml"
    config_path.write_text(
        f'[wheelhouse]\nallow = false\npath = "{wheelhouse_with_planted_wheel}"\n'
    )
    return config_path


@pytest.fixture
def named_config_allowing_the_default_path(wheelhouse_with_planted_wheel: Path) -> Path:
    wheelhouse_with_planted_wheel.rename(wheelhouse_with_planted_wheel.parent / "wheelhouse")
    config_path = wheelhouse_with_planted_wheel.parent / "named.toml"
    config_path.write_text("[wheelhouse]\nallow = true\n")
    return config_path


def _scan_rows(*extra_args: str) -> list[dict[str, str]]:
    result = CliRunner().invoke(main, ["scan", _PLANTED_GROUP, "--format", "JSON", *extra_args])
    assert result.exit_code == 0, result.output
    rows: list[dict[str, str]] = json.loads(result.stdout)
    return rows


class TestScanWheelhouse:
    @pytest.mark.parametrize(
        "case",
        [
            _ConfigFileCase(file_name="manager.toml"),
            _ConfigFileCase(file_name="agent.toml"),
            _ConfigFileCase(file_name="storage-proxy.toml"),
        ],
        ids=lambda case: case.file_name,
    )
    @pytest.mark.usefixtures("daemon_config_allowing_the_wheelhouse")
    def test_lists_the_wheels_of_a_daemon_config_allowing_it(self) -> None:
        assert _scan_rows() == [_WHEELHOUSE_ROW]

    def test_lists_the_wheels_of_a_named_config_allowing_it(
        self, named_config_allowing_the_wheelhouse: Path
    ) -> None:
        assert _scan_rows("-f", str(named_config_allowing_the_wheelhouse)) == [_WHEELHOUSE_ROW]

    def test_lists_the_wheels_in_the_default_path(
        self, named_config_allowing_the_default_path: Path
    ) -> None:
        assert _scan_rows("-f", str(named_config_allowing_the_default_path)) == [_WHEELHOUSE_ROW]

    def test_does_not_list_the_wheels_when_not_allowed(
        self, named_config_not_allowing_the_wheelhouse: Path
    ) -> None:
        assert _scan_rows("-f", str(named_config_not_allowing_the_wheelhouse)) == []

    @pytest.mark.usefixtures("wheelhouse_with_planted_wheel")
    def test_does_not_list_the_wheels_without_a_config(self) -> None:
        assert _scan_rows() == []
