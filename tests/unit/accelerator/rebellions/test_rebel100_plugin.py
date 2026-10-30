from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.accelerator.rebellions.common.atom_api import ATOMAPI, ATOMStat
from ai.backend.accelerator.rebellions.rebel100.plugin import Rebel100Plugin
from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, SlotName

_MODULE = "ai.backend.accelerator.rebellions.common.plugin"
_SLOT = SlotName("rebel100.device")


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
def patched_stats(stat_json: str) -> Iterator[None]:
    with patch.object(ATOMAPI, "get_stats", AsyncMock(return_value=ATOMStat.from_json(stat_json))):
        yield


class TestDeviceEnumeration:
    async def test_lists_devices_and_counts_whole_cards(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        devices = await plugin.list_devices()
        assert [d.device_id for d in devices] == ["rbln0", "rbln1", "rbln2", "rbln3"]
        assert all(isinstance(d, AbstractComputeDevice) for d in devices)
        assert devices[1].hw_location == "0000:f4:00.0"
        assert devices[0].memory_size == 150323855360
        assert await plugin.available_slots() == {_SLOT: Decimal(4)}

    async def test_device_name_must_match_exactly_and_warns_once(
        self, plugin: Rebel100Plugin, stat_payload: dict[str, Any]
    ) -> None:
        stat_payload["devices"][1]["name"] = "RBLN-CR130"
        stat_payload["devices"][2]["name"] = "RBLN-CA22"
        stats = ATOMStat.from_dict(stat_payload)
        with (
            patch.object(ATOMAPI, "get_stats", AsyncMock(return_value=stats)),
            patch("ai.backend.accelerator.rebellions.rebel100.plugin.log") as mock_log,
        ):
            devices = await plugin._list_devices()
            await plugin._list_devices()
        assert [d.device_id for d in devices] == ["rbln0", "rbln3"]
        assert mock_log.warning.call_count == 2


class TestContainerArgs:
    @pytest.mark.parametrize(
        ("allocation", "expected"),
        [
            ({"rbln1": 1}, ["rebellions.ai/npu=1"]),
            ({"rbln3": 1, "rbln2": 1}, ["rebellions.ai/npu=2", "rebellions.ai/npu=3"]),
            ({"rbln10": 1, "rbln2": 1}, ["rebellions.ai/npu=2", "rebellions.ai/npu=10"]),
            ({"rbln0": 0, "rbln2": 1}, ["rebellions.ai/npu=2"]),
        ],
        ids=["one-card", "two-cards", "numeric-order", "zero-allocation-skipped"],
    )
    async def test_cdi_requests_only_assigned_cards(
        self,
        plugin: Rebel100Plugin,
        patched_stats: None,
        allocation: dict[str, int],
        expected: list[str],
    ) -> None:
        args = await plugin.generate_docker_args(
            AsyncMock(),
            {_SLOT: {DeviceId(k): Decimal(v) for k, v in allocation.items()}},
        )
        host_config = args["HostConfig"]
        assert host_config["DeviceRequests"][0]["DeviceIDs"] == expected
        assert host_config["Devices"] == []

    async def test_no_allocation_requests_no_cards(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        args = await plugin.generate_docker_args(
            AsyncMock(), {_SLOT: {DeviceId("rbln1"): Decimal(0)}}
        )
        assert args["HostConfig"]["DeviceRequests"] == []

    async def test_cdi_kind_follows_configured_id(
        self, plugin: Rebel100Plugin, patched_stats: None
    ) -> None:
        plugin.cdi_device_id = "rebellions.ai/rebel100=runtime"
        args = await plugin.generate_docker_args(
            AsyncMock(), {_SLOT: {DeviceId("rbln0"): Decimal(1)}}
        )
        assert args["HostConfig"]["DeviceRequests"][0]["DeviceIDs"] == ["rebellions.ai/rebel100=0"]

    async def test_resource_data_env_var(self, plugin: Rebel100Plugin) -> None:
        plugin.device_ids_env_var = "REBEL_GLOBAL_DEVICE_IDS"
        data = await plugin.generate_resource_data({
            _SLOT: {DeviceId("rbln1"): Decimal(1), DeviceId("rbln0"): Decimal(1)},
        })
        assert data == {"REBEL_GLOBAL_DEVICE_IDS": "0:rbln0,1:rbln1"}


class TestContainerMeasures:
    @pytest.fixture
    def mock_docker(self, request: pytest.FixtureRequest) -> AsyncMock:
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
            ([], 0),
            (None, 0),
        ],
        indirect=["mock_docker"],
        ids=["two-cards", "foreign-cdi-id-ignored", "empty-requests", "null-requests"],
    )
    async def test_container_cards_come_from_cdi_ids(
        self,
        plugin: Rebel100Plugin,
        patched_stats: None,
        mock_docker: AsyncMock,
        expected_cards: int,
    ) -> None:
        with patch(f"{_MODULE}.Docker", return_value=mock_docker):
            mem, util = await plugin.gather_container_measures(MagicMock(), ["c1"])
        assert mem.per_container["c1"].capacity == Decimal(expected_cards * 150323855360)
        assert util.per_container["c1"].capacity == Decimal(expected_cards * 100)


class TestInit:
    @staticmethod
    def _new() -> Rebel100Plugin:
        plugin = Rebel100Plugin.__new__(Rebel100Plugin)
        plugin.plugin_config = {}
        return plugin

    async def test_reads_own_config_file(self) -> None:
        plugin = self._new()
        with (
            patch(
                f"{_MODULE}.config.read_from_file",
                return_value=({"general": {}}, Path("/etc/rebel100.toml")),
            ) as read_from_file,
            patch(f"{_MODULE}.shutil.which", return_value="/usr/bin/rbln-smi"),
            patch.object(Rebel100Plugin, "list_devices", AsyncMock(return_value=[])),
        ):
            await plugin.init()
        read_from_file.assert_called_once_with(None, "rebel100")

    @pytest.mark.parametrize(
        "raw_enable_rsd",
        [{}, {"enable_rsd": False}, {"enable_rsd": True}],
        ids=["default", "explicit-false", "explicit-true"],
    )
    async def test_rsd_is_always_off(self, raw_enable_rsd: dict[str, bool]) -> None:
        plugin = self._new()
        with (
            patch(
                f"{_MODULE}.config.read_from_file",
                return_value=({"general": {**raw_enable_rsd}}, Path("/etc/rebel100.toml")),
            ),
            patch(f"{_MODULE}.shutil.which", return_value="/usr/bin/rbln-smi"),
            patch.object(Rebel100Plugin, "list_devices", AsyncMock(return_value=[])),
        ):
            await plugin.init()
        assert plugin._enable_rsd is False

    async def test_searches_rbln_smi_before_rbln_stat(self) -> None:
        plugin = self._new()
        found = {"rbln-stat": "/usr/bin/rbln-stat", "rbln-smi": "/usr/bin/rbln-smi"}
        with (
            patch(
                f"{_MODULE}.config.read_from_file",
                return_value=({"general": {}}, Path("/etc/rebel100.toml")),
            ),
            patch(f"{_MODULE}.shutil.which", side_effect=found.get),
            patch.object(Rebel100Plugin, "list_devices", AsyncMock(return_value=[])),
        ):
            await plugin.init()
        assert plugin._rbln_stat_path == "/usr/bin/rbln-smi"

    async def test_missing_executable_reports_zero_slots(self) -> None:
        plugin = self._new()
        with (
            patch(
                f"{_MODULE}.config.read_from_file",
                return_value=({"general": {}}, Path("/etc/rebel100.toml")),
            ),
            patch(f"{_MODULE}.shutil.which", return_value=None),
        ):
            await plugin.init()
        assert await plugin.available_slots() == {_SLOT: Decimal(0)}
        measures = await plugin.gather_node_measures(MagicMock())
        assert all(m.per_node.value == 0 for m in measures)
