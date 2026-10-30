from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.accelerator.rebellions.atom_plus.plugin import ATOMPlusPlugin
from ai.backend.agent.resources import AbstractComputeDevice

_MODULE = "ai.backend.accelerator.rebellions.common.plugin"


def _new_plugin() -> ATOMPlusPlugin:
    plugin = ATOMPlusPlugin.__new__(ATOMPlusPlugin)
    plugin.plugin_config = {}
    return plugin


class TestStatPathConfig:
    @pytest.mark.parametrize("raw_general", [{}, {"rbln_stat_path": ""}], ids=["omitted", "blank"])
    async def test_unset_path_searches_path(self, raw_general: dict[str, Any]) -> None:
        plugin = _new_plugin()
        with (
            patch(
                f"{_MODULE}.config.read_from_file",
                return_value=({"general": raw_general}, Path("/etc/atom.toml")),
            ),
            patch(f"{_MODULE}.shutil.which", return_value="/usr/bin/rbln-stat"),
            patch.object(
                ATOMPlusPlugin,
                "list_devices",
                AsyncMock(return_value=[MagicMock(spec=AbstractComputeDevice)]),
            ),
        ):
            await plugin.init()
        assert plugin.enabled
        assert plugin._rbln_stat_path == "/usr/bin/rbln-stat"

    async def test_configured_path_skips_search(self) -> None:
        plugin = _new_plugin()
        with (
            patch(
                f"{_MODULE}.config.read_from_file",
                return_value=(
                    {"general": {"rbln_stat_path": "/opt/rbln/rbln-stat"}},
                    Path("/etc/atom.toml"),
                ),
            ),
            patch(f"{_MODULE}.shutil.which") as which,
            patch.object(ATOMPlusPlugin, "list_devices", AsyncMock(return_value=[])),
        ):
            await plugin.init()
        which.assert_not_called()
        assert plugin._rbln_stat_path == "/opt/rbln/rbln-stat"

    async def test_missing_executable_disables_and_reports_no_devices(self) -> None:
        plugin = _new_plugin()
        with (
            patch(
                f"{_MODULE}.config.read_from_file",
                return_value=({"general": {}}, Path("/etc/atom.toml")),
            ),
            patch(f"{_MODULE}.shutil.which", return_value=None),
        ):
            await plugin.init()
        assert not plugin.enabled
        assert await plugin.list_devices() == []
