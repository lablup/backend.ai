import sys
import tempfile
import textwrap as tw
import zipfile
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib.metadata import EntryPoint
from pathlib import Path

import pytest

from ai.backend.plugin.entrypoint import (
    extract_entrypoints_from_buildscript,
    match_plugin_list,
    prepare_wheelhouse,
    scan_entrypoint_from_buildscript,
    scan_entrypoint_from_plugin_checkouts,
)


def test_parse_build() -> None:
    with tempfile.NamedTemporaryFile("w") as f:
        f.write(
            tw.dedent(
                """
            python_sources(
                name="lib",
            )
            python_distribution(
                name="dist",
                dependencies=[
                    ":service",
                ],
                provides=python_artifact(
                    name="backend.ai-manager",
                    description="Backend.AI Manager",
                    license="LGPLv3",
                ),
                entry_points={
                    "backendai_cli_v10": {
                        "mgr": "ai.backend.manager.cli.__main__:main",
                        "mgr.start-server": "ai.backend.manager.server:main",
                    },
                    "backendai_hook_v20": {
                        "totp": "ai.backend.manager.plugin.totp.hook:TOTPHook",
                        "openid": "ai.backend.manager.plugin.openid.hook:OIDCHookPlugin",
                        "auth_keypair": "ai.backend.manager.plugin.keypair.hook:KeypairAuthHookPlugin",
                    },
                    "backendai_error_monitor_v20": {
                        "intrinsic": "ai.backend.manager.plugin.error_monitor:ErrorMonitor",
                    },
                },
                generate_setup=True,
            )
            python_tests(
                name="tests",
            )
        """
            )
        )
        f.flush()
        p = Path(f.name)
        items = [*extract_entrypoints_from_buildscript("backendai_cli_v10", p)]
        assert (items[0].name, items[0].module, items[0].attr) == (
            "mgr",
            "ai.backend.manager.cli.__main__",
            "main",
        )
        assert (items[1].name, items[1].module, items[1].attr) == (
            "mgr.start-server",
            "ai.backend.manager.server",
            "main",
        )
        items = [*extract_entrypoints_from_buildscript("backendai_hook_v20", p)]
        assert (items[0].name, items[0].module, items[0].attr) == (
            "totp",
            "ai.backend.manager.plugin.totp.hook",
            "TOTPHook",
        )
        assert (items[1].name, items[1].module, items[1].attr) == (
            "openid",
            "ai.backend.manager.plugin.openid.hook",
            "OIDCHookPlugin",
        )
        assert (items[2].name, items[2].module, items[2].attr) == (
            "auth_keypair",
            "ai.backend.manager.plugin.keypair.hook",
            "KeypairAuthHookPlugin",
        )
        items = [*extract_entrypoints_from_buildscript("backendai_error_monitor_v20", p)]
        assert (items[0].name, items[0].module, items[0].attr) == (
            "intrinsic",
            "ai.backend.manager.plugin.error_monitor",
            "ErrorMonitor",
        )


def test_match_blocklist() -> None:
    assert match_plugin_list("ai.backend.manager:abc", {"ai.backend.manager"})
    assert not match_plugin_list("ai.backend.manager:abc", {"ai.backend.agent"})
    assert match_plugin_list("ai.backend.manager.plugin.totp.hook:TOTPHook", {"ai.backend.manager"})
    assert not match_plugin_list("ai.backend.common.monitor:ErrorMonitor", {"ai.backend.manager"})


_PLANTED_GROUP = "backendai_planted_v1"
_PLANTED_WHEEL_STEM = "planted-1.0-py3-none-any"


@pytest.fixture
def discovery_environ_cleared(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_name in ("BACKEND_BUILD_ROOT", "BACKEND_WHEELHOUSE_PATH", "SCIE"):
        monkeypatch.delenv(env_name, raising=False)


@pytest.fixture
def directory_with_planted_wheel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    wheelhouse_path = tmp_path / "wheelhouse"
    wheelhouse_path.mkdir()
    with zipfile.ZipFile(wheelhouse_path / f"{_PLANTED_WHEEL_STEM}.whl", "w") as wheel:
        wheel.writestr("planted.py", "")
    monkeypatch.setattr(sys, "path", [*sys.path])
    return tmp_path


@pytest.fixture
def directory_with_planted_build_files(tmp_path: Path) -> Path:
    (tmp_path / "BUILD_ROOT").touch()
    for build_file_parent in (tmp_path / "src" / "planted", tmp_path / "plugins" / "planted"):
        build_file_parent.mkdir(parents=True)
        (build_file_parent / "BUILD").write_text(
            f'python_distribution(entry_points={{"{_PLANTED_GROUP}": {{"planted": "planted:Plugin"}}}})'
        )
    return tmp_path


@dataclass(frozen=True)
class _ExplicitWheelhouseCase:
    env_name: str
    env_path_under_directory: str


@pytest.fixture
def current_directory_with_planted_wheel(
    directory_with_planted_wheel: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.chdir(directory_with_planted_wheel)
    return directory_with_planted_wheel


@pytest.fixture
def current_directory_without_wheels(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def wheel_on_the_configured_path(
    case: _ExplicitWheelhouseCase,
    discovery_environ_cleared: None,
    directory_with_planted_wheel: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    monkeypatch.setenv(
        case.env_name, str(directory_with_planted_wheel / case.env_path_under_directory)
    )
    return directory_with_planted_wheel


@pytest.fixture
def current_directory_holding_the_configured_wheelhouse(
    wheel_on_the_configured_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(wheel_on_the_configured_path)


@pytest.fixture
def current_directory_under_planted_build_root(
    directory_with_planted_build_files: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(directory_with_planted_build_files / "src")


@pytest.fixture
def build_root_named_by_the_environment(
    discovery_environ_cleared: None,
    directory_with_planted_build_files: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("BACKEND_BUILD_ROOT", str(directory_with_planted_build_files))


@pytest.mark.usefixtures("discovery_environ_cleared")
class TestPrepareWheelhouse:
    def test_ignores_wheels_in_the_current_directory(
        self, current_directory_with_planted_wheel: Path
    ) -> None:
        prepare_wheelhouse()

        extracted_path = current_directory_with_planted_wheel / "wheelhouse" / _PLANTED_WHEEL_STEM
        assert not extracted_path.exists()
        assert str(extracted_path) not in sys.path

    def test_warns_about_wheels_ignored_in_the_current_directory(
        self, current_directory_with_planted_wheel: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        prepare_wheelhouse()

        assert "BACKEND_WHEELHOUSE_PATH" in caplog.text

    @pytest.mark.usefixtures("current_directory_without_wheels")
    def test_does_not_warn_without_wheels_in_the_current_directory(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        prepare_wheelhouse()

        assert "BACKEND_WHEELHOUSE_PATH" not in caplog.text

    @pytest.mark.parametrize(
        "case",
        [
            _ExplicitWheelhouseCase(
                env_name="BACKEND_WHEELHOUSE_PATH", env_path_under_directory="wheelhouse"
            ),
            _ExplicitWheelhouseCase(env_name="BACKEND_BUILD_ROOT", env_path_under_directory="."),
        ],
        ids=lambda case: case.env_name,
    )
    @pytest.mark.usefixtures("current_directory_holding_the_configured_wheelhouse")
    def test_does_not_warn_when_the_current_directory_holds_the_configured_wheelhouse(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        prepare_wheelhouse()

        assert "BACKEND_WHEELHOUSE_PATH" not in caplog.text

    @pytest.mark.parametrize(
        "case",
        [
            _ExplicitWheelhouseCase(
                env_name="BACKEND_WHEELHOUSE_PATH", env_path_under_directory="wheelhouse"
            ),
            _ExplicitWheelhouseCase(env_name="BACKEND_BUILD_ROOT", env_path_under_directory="."),
        ],
        ids=lambda case: case.env_name,
    )
    def test_loads_wheels_from_the_configured_path(
        self, wheel_on_the_configured_path: Path
    ) -> None:
        prepare_wheelhouse()

        extracted_path = wheel_on_the_configured_path / "wheelhouse" / _PLANTED_WHEEL_STEM
        assert (extracted_path / "planted.py").exists()
        assert any(Path(entry) == extracted_path for entry in sys.path)


@pytest.mark.parametrize(
    "scan_build_root",
    [scan_entrypoint_from_buildscript, scan_entrypoint_from_plugin_checkouts],
    ids=lambda scanner: scanner.__name__,
)
@pytest.mark.usefixtures("discovery_environ_cleared")
class TestBuildRootDiscovery:
    @pytest.mark.usefixtures("current_directory_under_planted_build_root")
    def test_ignores_a_build_root_above_the_current_directory(
        self, scan_build_root: Callable[[str], Iterator[EntryPoint]]
    ) -> None:
        entrypoints = [*scan_build_root(_PLANTED_GROUP)]

        assert entrypoints == []

    @pytest.mark.usefixtures("build_root_named_by_the_environment")
    def test_reads_the_build_root_named_by_the_environment(
        self, scan_build_root: Callable[[str], Iterator[EntryPoint]]
    ) -> None:
        entrypoints = [*scan_build_root(_PLANTED_GROUP)]

        assert [entrypoint.name for entrypoint in entrypoints] == ["planted"]
