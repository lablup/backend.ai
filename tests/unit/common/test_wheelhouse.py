import sys
import zipfile
from pathlib import Path

import pytest

from ai.backend.common.configs.wheelhouse import WheelhouseConfig
from ai.backend.common.plugin import load_configured_wheelhouse

_PLANTED_WHEEL_STEM = "planted-1.0-py3-none-any"
_NOT_LOADED_WARNING = "wheels in ./wheelhouse not loaded"


@pytest.fixture
def directory_with_planted_wheel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    wheelhouse_path = tmp_path / "wheelhouse"
    wheelhouse_path.mkdir()
    with zipfile.ZipFile(wheelhouse_path / f"{_PLANTED_WHEEL_STEM}.whl", "w") as wheel:
        wheel.writestr("planted.py", "")
    monkeypatch.setattr(sys, "path", [*sys.path])
    return tmp_path


@pytest.fixture
def current_directory_with_planted_wheel(
    directory_with_planted_wheel: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.chdir(directory_with_planted_wheel)
    return directory_with_planted_wheel


@pytest.fixture
def current_directory_without_wheels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


class TestWheelhouseConfig:
    def test_does_not_allow_by_default(self) -> None:
        assert WheelhouseConfig.model_validate({}).allow is False

    def test_uses_wheelhouse_under_the_current_directory_by_default(self) -> None:
        assert WheelhouseConfig.model_validate({}).path == Path("wheelhouse")


class TestLoadConfiguredWheelhouse:
    def test_loads_the_wheels_in_the_configured_path_when_allowed(
        self, directory_with_planted_wheel: Path
    ) -> None:
        wheelhouse_path = directory_with_planted_wheel / "wheelhouse"

        load_configured_wheelhouse(WheelhouseConfig(allow=True, path=wheelhouse_path))

        extracted_path = wheelhouse_path / _PLANTED_WHEEL_STEM
        assert (extracted_path / "planted.py").exists()
        assert str(extracted_path) in sys.path

    def test_loads_the_wheels_in_the_current_directory_by_default_when_allowed(
        self, current_directory_with_planted_wheel: Path
    ) -> None:
        load_configured_wheelhouse(WheelhouseConfig.model_validate({"allow": True}))

        extracted_path = (
            current_directory_with_planted_wheel / "wheelhouse" / _PLANTED_WHEEL_STEM
        ).resolve()
        assert (extracted_path / "planted.py").exists()
        assert str(extracted_path) in sys.path

    def test_does_not_load_the_wheels_in_the_configured_path_when_not_allowed(
        self, directory_with_planted_wheel: Path
    ) -> None:
        wheelhouse_path = directory_with_planted_wheel / "wheelhouse"

        load_configured_wheelhouse(WheelhouseConfig(allow=False, path=wheelhouse_path))

        extracted_path = wheelhouse_path / _PLANTED_WHEEL_STEM
        assert not extracted_path.exists()
        assert str(extracted_path) not in sys.path

    def test_warns_about_wheels_in_the_current_directory_when_not_allowed(
        self, current_directory_with_planted_wheel: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        load_configured_wheelhouse(WheelhouseConfig.model_validate({}))

        assert _NOT_LOADED_WARNING in caplog.text
        extracted_path = current_directory_with_planted_wheel / "wheelhouse" / _PLANTED_WHEEL_STEM
        assert not extracted_path.exists()

    @pytest.mark.usefixtures("current_directory_without_wheels")
    def test_does_not_warn_without_wheels_in_the_current_directory(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        load_configured_wheelhouse(WheelhouseConfig.model_validate({}))

        assert _NOT_LOADED_WARNING not in caplog.text
