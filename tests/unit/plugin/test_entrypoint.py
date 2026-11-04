import sys
import tempfile
import textwrap as tw
import zipfile
from pathlib import Path

import pytest

from ai.backend.plugin.entrypoint import (
    extract_entrypoints_from_buildscript,
    match_plugin_list,
    prepare_wheelhouse,
    scan_entrypoint_from_wheelhouse,
    scan_entrypoints,
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
def directory_with_planted_wheel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    wheelhouse_path = tmp_path / "wheelhouse"
    wheelhouse_path.mkdir()
    with zipfile.ZipFile(wheelhouse_path / f"{_PLANTED_WHEEL_STEM}.whl", "w") as wheel:
        wheel.writestr("planted.py", "")
        wheel.writestr(
            "planted-1.0.dist-info/METADATA",
            "Metadata-Version: 2.1\nName: planted\nVersion: 1.0\n",
        )
        wheel.writestr(
            "planted-1.0.dist-info/entry_points.txt",
            f"[{_PLANTED_GROUP}]\nplanted = planted:Plugin\n",
        )
    monkeypatch.setattr(sys, "path", [*sys.path])
    return tmp_path


@pytest.fixture
def current_directory_with_planted_wheel(
    directory_with_planted_wheel: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    monkeypatch.chdir(directory_with_planted_wheel)
    return directory_with_planted_wheel


class TestWheelLoading:
    def test_scanning_does_not_load_wheels_in_the_current_directory(
        self, current_directory_with_planted_wheel: Path
    ) -> None:
        entrypoints = [*scan_entrypoints(_PLANTED_GROUP)]

        extracted_path = current_directory_with_planted_wheel / "wheelhouse" / _PLANTED_WHEEL_STEM
        assert entrypoints == []
        assert not extracted_path.exists()
        assert str(extracted_path) not in sys.path

    def test_scanning_a_wheelhouse_reads_entry_points_without_loading_the_wheels(
        self, directory_with_planted_wheel: Path
    ) -> None:
        wheelhouse_path = directory_with_planted_wheel / "wheelhouse"

        entrypoints = [*scan_entrypoint_from_wheelhouse(_PLANTED_GROUP, wheelhouse_path)]

        extracted_path = wheelhouse_path / _PLANTED_WHEEL_STEM
        assert [entrypoint.name for entrypoint in entrypoints] == ["planted"]
        assert not extracted_path.exists()
        assert str(extracted_path) not in sys.path

    def test_prepare_wheelhouse_loads_the_wheels_in_the_given_path(
        self, directory_with_planted_wheel: Path
    ) -> None:
        prepare_wheelhouse(directory_with_planted_wheel / "wheelhouse")

        extracted_path = directory_with_planted_wheel / "wheelhouse" / _PLANTED_WHEEL_STEM
        assert (extracted_path / "planted.py").exists()
        assert any(Path(entry) == extracted_path for entry in sys.path)
