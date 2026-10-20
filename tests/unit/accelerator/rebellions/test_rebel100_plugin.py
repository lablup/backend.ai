from __future__ import annotations

import json
import stat
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.accelerator.rebellions.atom.plugin import ATOMPlugin
from ai.backend.accelerator.rebellions.atom_max.plugin import ATOMMaxPlugin
from ai.backend.accelerator.rebellions.atom_plus.plugin import ATOMPlusPlugin
from ai.backend.accelerator.rebellions.common.atom_api import ATOMAPI, ATOMStat, LibraryError
from ai.backend.accelerator.rebellions.common.plugin import AbstractATOMPlugin
from ai.backend.accelerator.rebellions.rebel100.plugin import Rebel100Plugin
from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, SlotName


def _make_tool(tmp_path: Path, name: str, body: str) -> str:
    path = tmp_path / name
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


@pytest.fixture
def smi_json_text(idle_group_json: dict[str, Any]) -> str:
    return json.dumps(idle_group_json)


@pytest.fixture
def plugin() -> Rebel100Plugin:
    plugin = Rebel100Plugin.__new__(Rebel100Plugin)
    plugin.plugin_config = {}
    plugin.enabled = True
    plugin.device_mask = []
    plugin._rbln_stat_path = "/usr/bin/rbln-smi"
    plugin._all_devices = None
    plugin._enable_rsd = False
    plugin._unknown_device_names = set()
    plugin.atom_config = {
        "general": {"enforce_singular_numa_affinity": False, "enable_rsd": False},
    }
    return plugin


@pytest.fixture
def patched_stats(smi_json_text: str) -> Iterator[None]:
    stats = ATOMStat.from_json(smi_json_text)
    with patch.object(ATOMAPI, "get_stats", AsyncMock(return_value=stats)):
        yield


class TestRebelPluginIdentity:
    def test_key_slot_and_config_name(self, plugin: Rebel100Plugin) -> None:
        assert plugin.key == "rebel100"
        assert plugin.slot_types == ((SlotName("rebel100.device"), "count"),)
        assert plugin.exclusive_slot_types == {"rebel100.device"}
        assert plugin.config_name == "rebel100"
        assert plugin.executable_names == ("rbln-smi", "rbln-stat")
        assert plugin.stat_args == ("-g", "-j")
        assert plugin.device_names == ("RBLN-CR13",)
        assert plugin.enable_rsd_default is False

    def test_atom_plugins_keep_their_config_name_and_defaults(self) -> None:
        # Regression check for the shared base class.
        assert AbstractATOMPlugin.config_name == "atom"
        assert ATOMPlusPlugin.config_name == "atom"
        assert ATOMPlusPlugin.executable_names == ("rbln-stat",)
        assert ATOMPlusPlugin.stat_args == ("-g", "-j")
        assert ATOMPlusPlugin.cdi_device_id == "rebellions.ai/npu=runtime"
        assert ATOMPlusPlugin.device_ids_env_var == "ATOM_GLOBAL_DEVICE_IDS"

    def test_metadata(self, plugin: Rebel100Plugin) -> None:
        assert plugin.get_metadata()["slot_name"] == "rebel100.device"


class TestRebelDeviceEnumeration:
    async def test_lists_only_rebel100_devices(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        devices = await plugin.list_devices()
        assert [d.device_id for d in devices] == ["rbln0", "rbln1", "rbln2", "rbln3"]
        assert all(isinstance(d, AbstractComputeDevice) for d in devices)
        assert devices[0].memory_size == 150323855360
        assert devices[1].hw_location == "0000:f4:00.0"
        assert devices[0].model_name == "RBLN-CR13"

    async def test_available_slots_counts_whole_cards(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        assert await plugin.available_slots() == {SlotName("rebel100.device"): Decimal(4)}

    async def test_device_name_must_match_exactly(
        self, plugin: Rebel100Plugin, idle_group_json: dict[str, Any]
    ) -> None:
        data = idle_group_json
        data["devices"][1]["name"] = "RBLN-CR130"
        data["devices"][2]["name"] = "RBLN-CA22"
        stats = ATOMStat.from_dict(data)
        with (
            patch.object(ATOMAPI, "get_stats", AsyncMock(return_value=stats)),
            patch("ai.backend.accelerator.rebellions.rebel100.plugin.log") as mock_log,
        ):
            devices = await plugin._list_devices()
            await plugin._list_devices()
        assert [d.device_id for d in devices] == ["rbln0", "rbln3"]
        assert mock_log.warning.call_count == 2

    async def test_device_files(self, plugin: Rebel100Plugin, patched_stats: None) -> None:
        device = (await plugin.list_devices())[1]
        assert list(await plugin.list_device_files(device)) == ["/dev/rbln1"]

    def test_output_without_group_flag_lacks_group_id(self, loaded_json: dict[str, Any]) -> None:
        # Why `stat_args` carries `-g`: plain `-j` (here under load) has no `group_id`.
        assert loaded_json["contexts"][0]["npu"] == 1
        with pytest.raises(KeyError, match="group_id"):
            ATOMStat.from_dict(loaded_json)


class TestRebelContainerArgs:
    @pytest.mark.parametrize(
        ("assigned", "expected"),
        [
            (["rbln1"], ["rebellions.ai/npu=1"]),
            (["rbln3", "rbln2"], ["rebellions.ai/npu=2", "rebellions.ai/npu=3"]),
        ],
        ids=["one-card", "two-cards"],
    )
    async def test_cdi_requests_only_assigned_cards(
        self,
        plugin: Rebel100Plugin,
        patched_stats: None,
        assigned: list[str],
        expected: list[str],
    ) -> None:
        plugin.cdi_device_id = "rebellions.ai/npu=runtime"
        args = await plugin.generate_docker_args(
            AsyncMock(),
            {SlotName("rebel100.device"): {DeviceId(d): Decimal(1) for d in assigned}},
        )
        host_config = args["HostConfig"]
        assert host_config["DeviceRequests"][0]["DeviceIDs"] == expected
        assert "IPC_LOCK" in host_config["CapAdd"]

    async def test_cdi_kind_follows_configured_id(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        plugin.cdi_device_id = "rebellions.ai/rebel100=runtime"
        args = await plugin.generate_docker_args(
            AsyncMock(),
            {SlotName("rebel100.device"): {DeviceId("rbln0"): Decimal(1)}},
        )
        assert args["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == ["rebellions.ai/rebel100=0"]

    async def test_rbln_and_rsd_device_files_are_dropped(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        args = await plugin.generate_docker_args(
            AsyncMock(),
            {SlotName("rebel100.device"): {DeviceId("rbln1"): Decimal(1)}},
        )
        assert args["HostConfig"]["Devices"] == []

    async def test_zero_allocation_requests_no_cards(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        args = await plugin.generate_docker_args(
            AsyncMock(),
            {SlotName("rebel100.device"): {DeviceId("rbln1"): Decimal(0)}},
        )
        assert args["HostConfig"]["DeviceRequests"] == []

    async def test_zero_allocation_cards_are_skipped(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        args = await plugin.generate_docker_args(
            AsyncMock(),
            {
                SlotName("rebel100.device"): {
                    DeviceId("rbln0"): Decimal(0),
                    DeviceId("rbln2"): Decimal(1),
                }
            },
        )
        assert args["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == ["rebellions.ai/npu=2"]

    async def test_cdi_ids_come_from_allocation_sorted_numerically(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        args = await plugin.generate_docker_args(
            AsyncMock(),
            {
                SlotName("rebel100.device"): {
                    DeviceId("rbln10"): Decimal(1),
                    DeviceId("rbln2"): Decimal(1),
                }
            },
        )
        assert args["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == [
            "rebellions.ai/npu=2",
            "rebellions.ai/npu=10",
        ]

    async def test_default_env_var(self, plugin: Rebel100Plugin) -> None:
        data = await plugin.generate_resource_data({
            SlotName("rebel100.device"): {DeviceId("rbln3"): Decimal(1)},
        })
        assert data == {"ATOM_GLOBAL_DEVICE_IDS": "0:rbln3"}

    async def test_configured_env_var(self, plugin: Rebel100Plugin) -> None:
        plugin.device_ids_env_var = "REBEL_GLOBAL_DEVICE_IDS"
        data = await plugin.generate_resource_data({
            SlotName("rebel100.device"): {
                DeviceId("rbln1"): Decimal(1),
                DeviceId("rbln0"): Decimal(1),
            },
        })
        assert data == {"REBEL_GLOBAL_DEVICE_IDS": "0:rbln0,1:rbln1"}


class TestRebelContainerMeasures:
    @pytest.fixture
    def mock_docker(self, request: pytest.FixtureRequest) -> AsyncMock:
        # CDI-only container: the cards appear in DeviceRequests, not in Devices.
        container_info = {"HostConfig": {"Devices": [], "DeviceRequests": request.param}}
        docker = AsyncMock()
        docker.__aenter__ = AsyncMock(return_value=docker)
        docker.__aexit__ = AsyncMock(return_value=False)
        docker.containers.get = AsyncMock(return_value=container_info)
        return docker

    @pytest.mark.parametrize(
        ("mock_docker", "expected_cards"),
        [
            ([{"Driver": "cdi", "DeviceIDs": ["rebellions.ai/npu=1", "rebellions.ai/npu=3"]}], 2),
            ([{"Driver": "cdi", "DeviceIDs": ["rebellions.ai/npu=3", "x/gpu=1"]}], 1),
            ([{"Driver": "cdi", "DeviceIDs": ["x/gpu=1"]}], 0),
            ([], 0),
            (None, 0),
        ],
        indirect=["mock_docker"],
        ids=[
            "two-cards",
            "foreign-cdi-id-ignored",
            "foreign-only",
            "empty-requests",
            "null-requests",
        ],
    )
    async def test_container_cards_come_from_cdi_ids(
        self,
        plugin: Rebel100Plugin,
        patched_stats: None,
        mock_docker: AsyncMock,
        expected_cards: int,
    ) -> None:
        with patch(
            "ai.backend.accelerator.rebellions.common.plugin.Docker", return_value=mock_docker
        ):
            mem, util = await plugin.gather_container_measures(MagicMock(), ["c1"])
        assert mem.per_container["c1"].capacity == Decimal(expected_cards * 150323855360)
        assert util.per_container["c1"].capacity == Decimal(expected_cards * 100)


class TestATOMAPIToolHandling:
    @pytest.fixture
    def payload(self, tmp_path: Path, smi_json_text: str) -> Path:
        path = tmp_path / "out.json"
        path.write_text(smi_json_text)
        return path

    async def test_custom_stat_args_and_parsing(self, tmp_path: Path, payload: Path) -> None:
        tool = _make_tool(tmp_path, "rbln-smi", f'echo "$@" > {tmp_path}/args; cat {payload}')
        stats = await ATOMAPI.get_stats(tool, ("-j",))
        assert stats.KMD_version == "3.5.1"
        assert len(stats.devices) == 4
        assert (tmp_path / "args").read_text().strip() == "-j"

    async def test_default_stat_args_ignore_binary_name(
        self, tmp_path: Path, payload: Path
    ) -> None:
        tool = _make_tool(tmp_path, "rbln-smi", f'echo "$@" > {tmp_path}/args; cat {payload}')
        await ATOMAPI.get_stats(tool)
        assert (tmp_path / "args").read_text().strip() == "-g -j"

    async def test_atom_plugin_with_rbln_smi_named_binary_keeps_group_flag(
        self, tmp_path: Path, payload: Path
    ) -> None:
        tool = _make_tool(tmp_path, "rbln-smi", f'echo "$@" > {tmp_path}/args; cat {payload}')
        atom_plus = ATOMPlusPlugin.__new__(ATOMPlusPlugin)
        atom_plus._rbln_stat_path = tool
        devices = await atom_plus._list_devices()
        assert devices == []
        assert (tmp_path / "args").read_text().strip() == "-g -j"

    async def test_stderr_warning_with_zero_exit_is_not_fatal(
        self, tmp_path: Path, payload: Path
    ) -> None:
        tool = _make_tool(tmp_path, "rbln-smi", f"echo 'warning: x' >&2; cat {payload}")
        stats = await ATOMAPI.get_stats(tool)
        assert len(stats.devices) == 4

    async def test_nonzero_exit_raises(self, tmp_path: Path) -> None:
        tool = _make_tool(tmp_path, "rbln-smi", "echo boom >&2; exit 3")
        with pytest.raises(LibraryError, match="exit code 3"):
            await ATOMAPI.get_stats(tool)

    async def test_group_command_stderr_is_fatal(self, tmp_path: Path, payload: Path) -> None:
        tool = _make_tool(
            tmp_path, "rbln-smi", f'case "$1" in group) echo bad >&2;; *) cat {payload};; esac'
        )
        with pytest.raises(LibraryError):
            await ATOMAPI.create_group(tool, [0, 1])

    async def test_create_group_picks_free_id(self, tmp_path: Path, payload: Path) -> None:
        tool = _make_tool(tmp_path, "rbln-smi", f'echo "$@" >> {tmp_path}/args; cat {payload}')
        group_id = await ATOMAPI.create_group(tool, [0, 1])
        assert group_id == 1
        assert "group -c 1 -a 0,1" in (tmp_path / "args").read_text()


class TestConfigName:
    @pytest.mark.parametrize(
        ("plugin_cls", "expected"),
        [
            (ATOMPlugin, "atom"),
            (ATOMPlusPlugin, "atom"),
            (ATOMMaxPlugin, "atom"),
            (Rebel100Plugin, "rebel100"),
        ],
        ids=["atom", "atom-plus", "atom-max", "rebel100"],
    )
    async def test_init_reads_own_config_file(
        self, plugin_cls: type[AbstractATOMPlugin[Any]], expected: str
    ) -> None:
        plugin = plugin_cls.__new__(plugin_cls)
        plugin.plugin_config = {}
        raw_cfg: dict[str, Any] = {"general": {}}
        with (
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.config.read_from_file",
                return_value=(raw_cfg, Path("/etc/x.toml")),
            ) as read_from_file,
            patch("ai.backend.accelerator.rebellions.common.plugin.shutil.which") as which,
            patch.object(plugin_cls, "list_devices", AsyncMock(return_value=[])),
        ):
            which.return_value = "/usr/bin/rbln-tool"
            await plugin.init()
        read_from_file.assert_called_once_with(None, expected)
        assert plugin.enabled

    @pytest.mark.parametrize(
        "raw_enable_rsd",
        [{}, {"enable_rsd": False}, {"enable_rsd": True}],
        ids=["default", "explicit-false", "explicit-true"],
    )
    async def test_rebel100_forces_rsd_off(self, raw_enable_rsd: dict[str, bool]) -> None:
        plugin = Rebel100Plugin.__new__(Rebel100Plugin)
        plugin.plugin_config = {}
        raw_cfg = {"general": {**raw_enable_rsd}}
        with (
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.config.read_from_file",
                return_value=(raw_cfg, Path("/etc/rebel100.toml")),
            ),
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.shutil.which",
                return_value="/usr/bin/rbln-smi",
            ),
            patch.object(Rebel100Plugin, "list_devices", AsyncMock(return_value=[])),
        ):
            await plugin.init()
        assert plugin._enable_rsd is False

    def test_atom_enable_rsd_stays_on_by_default(self) -> None:
        assert ATOMPlugin.enable_rsd_default is True


class TestStatPathConfig:
    @pytest.mark.parametrize(
        "raw_general",
        [{}, {"rbln_stat_path": ""}],
        ids=["omitted", "blank"],
    )
    async def test_unset_path_searches_path(self, raw_general: dict[str, str]) -> None:
        plugin = Rebel100Plugin.__new__(Rebel100Plugin)
        plugin.plugin_config = {}
        with (
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.config.read_from_file",
                return_value=({"general": raw_general}, Path("/etc/rebel100.toml")),
            ),
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.shutil.which",
                side_effect=lambda name: "/usr/bin/rbln-smi" if name == "rbln-smi" else None,
            ),
            patch.object(Rebel100Plugin, "list_devices", AsyncMock(return_value=[])),
        ):
            await plugin.init()
        assert plugin.enabled
        assert plugin._rbln_stat_path == "/usr/bin/rbln-smi"

    async def test_configured_path_skips_search(self) -> None:
        plugin = Rebel100Plugin.__new__(Rebel100Plugin)
        plugin.plugin_config = {}
        with (
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.config.read_from_file",
                return_value=(
                    {"general": {"rbln_stat_path": "/opt/rbln/rbln-smi"}},
                    Path("/etc/rebel100.toml"),
                ),
            ),
            patch("ai.backend.accelerator.rebellions.common.plugin.shutil.which") as which,
            patch.object(Rebel100Plugin, "list_devices", AsyncMock(return_value=[])),
        ):
            await plugin.init()
        which.assert_not_called()
        assert plugin._rbln_stat_path == "/opt/rbln/rbln-smi"

    async def test_missing_executable_disables_and_skips_node_stats(self) -> None:
        plugin = Rebel100Plugin.__new__(Rebel100Plugin)
        plugin.plugin_config = {}
        with (
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.config.read_from_file",
                return_value=({"general": {}}, Path("/etc/rebel100.toml")),
            ),
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.shutil.which",
                return_value=None,
            ),
        ):
            await plugin.init()
        assert not plugin.enabled
        measures = await plugin.gather_node_measures(MagicMock())
        assert all(m.per_node.value == 0 for m in measures)
