from __future__ import annotations

import json
import stat
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import trafaret as t

from ai.backend.accelerator.rebellions.atom.plugin import ATOMPlugin
from ai.backend.accelerator.rebellions.atom_max.plugin import ATOMMaxPlugin
from ai.backend.accelerator.rebellions.atom_plus.plugin import ATOMPlusPlugin
from ai.backend.accelerator.rebellions.common.atom_api import ATOMAPI, ATOMStat, LibraryError
from ai.backend.accelerator.rebellions.common.plugin import AbstractATOMPlugin
from ai.backend.accelerator.rebellions.rebel100.plugin import Rebel100Plugin
from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, SlotName

# Synthetic fixture: the real Rebel100 `rbln-smi -j` output is not available yet.
SYNTHETIC_REBEL_SMI_JSON = {
    "KMD_version": "3.2.2",
    "devices": [
        {
            "group_id": "0",
            "npu": 0,
            "name": "RBLN-CR03",
            "sid": "sid-0",
            "uuid": "uuid-0",
            "device": "rbln0",
            "pci": {
                "bus_id": "0000:41:00.0",
                "numa_node": 0,
                "link_speed": "32.0 GT/s",
                "link_width": "16",
            },
            "temperature": "40",
            "memory": {"used": "1000", "total": str(144 * 1024**3)},
            "util": "12",
            "card_power": "100000000",
            "extra_new_field": "ignored",
        },
        {
            "group_id": "0",
            "npu": 1,
            "name": "RBLN-CR03",
            "sid": "sid-1",
            "uuid": "uuid-1",
            "device": "rbln1",
            "pci": {
                "bus_id": "0000:c1:00.0",
                "numa_node": 1,
                "link_speed": "32.0 GT/s",
                "link_width": "16",
            },
            "temperature": "41",
            "memory": {"used": "2000", "total": str(144 * 1024**3)},
            "util": "34",
        },
        {
            "group_id": "0",
            "npu": 2,
            "name": "RBLN-CA22",
            "sid": None,
            "uuid": "uuid-2",
            "device": "rbln2",
            "pci": {
                "bus_id": "0000:81:00.0",
                "numa_node": 1,
                "link_speed": "16.0 GT/s",
                "link_width": "16",
            },
            "temperature": "42",
            "memory": {"used": "0", "total": "1000"},
            "util": "0",
        },
    ],
}


def _make_tool(tmp_path: Path, name: str, body: str) -> str:
    path = tmp_path / name
    path.write_text(f"#!/bin/sh\n{body}\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


@pytest.fixture
def smi_json_text() -> str:
    return json.dumps(SYNTHETIC_REBEL_SMI_JSON)


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
        assert plugin.stat_args == ("-j",)

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
        assert [d.device_id for d in devices] == ["rbln0", "rbln1"]
        assert all(isinstance(d, AbstractComputeDevice) for d in devices)
        assert devices[0].memory_size == 144 * 1024**3
        assert devices[1].numa_node == 1
        assert devices[0].model_name == "RBLN-CR03"

    async def test_available_slots_counts_whole_cards(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        assert await plugin.available_slots() == {SlotName("rebel100.device"): Decimal(2)}

    async def test_unknown_device_name_is_logged_once(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        with patch("ai.backend.accelerator.rebellions.rebel100.plugin.log") as mock_log:
            await plugin._list_devices()
            await plugin._list_devices()
        assert mock_log.warning.call_count == 1
        assert mock_log.warning.call_args.kwargs["device_name"] == "RBLN-CA22"

    async def test_configured_device_names_override_prefix(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        plugin.atom_config["general"]["device_names"] = ["RBLN-CA22"]
        devices = await plugin._list_devices()
        assert [d.device_id for d in devices] == ["rbln2"]

    async def test_device_files(self, plugin: Rebel100Plugin, patched_stats: None) -> None:
        device = (await plugin.list_devices())[1]
        assert list(await plugin.list_device_files(device)) == ["/dev/rbln1"]


class TestRebelContainerArgs:
    async def test_generate_docker_args_whole_card(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        args = await plugin.generate_docker_args(
            AsyncMock(),
            {SlotName("rebel100.device"): {DeviceId("rbln1"): Decimal(1)}},
        )
        host_config = args["HostConfig"]
        assert host_config["Devices"] == [
            {
                "PathOnHost": "/dev/rbln1",
                "PathInContainer": "/dev/rbln0",
                "CgroupPermissions": "rwm",
            }
        ]
        assert host_config["DeviceRequests"][0]["DeviceIDs"] == ["rebellions.ai/npu=runtime"]
        assert "IPC_LOCK" in host_config["CapAdd"]

    async def test_configured_cdi_id(self, plugin: Rebel100Plugin, patched_stats: None) -> None:
        plugin.cdi_device_id = "rebellions.ai/rebel100=runtime"
        args = await plugin.generate_docker_args(
            AsyncMock(),
            {SlotName("rebel100.device"): {DeviceId("rbln0"): Decimal(1)}},
        )
        assert args["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == [
            "rebellions.ai/rebel100=runtime"
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


class TestATOMAPIToolHandling:
    @pytest.fixture
    def payload(self, tmp_path: Path, smi_json_text: str) -> Path:
        path = tmp_path / "out.json"
        path.write_text(smi_json_text)
        return path

    async def test_custom_stat_args_and_parsing(self, tmp_path: Path, payload: Path) -> None:
        tool = _make_tool(tmp_path, "rbln-smi", f'echo "$@" > {tmp_path}/args; cat {payload}')
        stats = await ATOMAPI.get_stats(tool, ("-j",))
        assert stats.KMD_version == "3.2.2"
        assert len(stats.devices) == 3
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
        assert [d.device_id for d in devices] == ["rbln2"]
        assert (tmp_path / "args").read_text().strip() == "-g -j"

    async def test_stderr_warning_with_zero_exit_is_not_fatal(
        self, tmp_path: Path, payload: Path
    ) -> None:
        tool = _make_tool(tmp_path, "rbln-smi", f"echo 'warning: x' >&2; cat {payload}")
        stats = await ATOMAPI.get_stats(tool)
        assert len(stats.devices) == 3

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
        raw_cfg = {"general": {"rbln_stat_path": None}}
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

    async def test_device_names_must_be_a_list(self) -> None:
        plugin = Rebel100Plugin.__new__(Rebel100Plugin)
        plugin.plugin_config = {}
        raw_cfg = {"general": {"rbln_stat_path": None, "device_names": "RBLN-CR03"}}
        with (
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.config.read_from_file",
                return_value=(raw_cfg, Path("/etc/rebel100.toml")),
            ),
            pytest.raises(t.DataError),
        ):
            await plugin.init()
