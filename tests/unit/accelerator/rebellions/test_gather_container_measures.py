from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.backend.accelerator.rebellions.atom.plugin import ATOMPlugin
from ai.backend.accelerator.rebellions.atom_max.plugin import ATOMMaxPlugin
from ai.backend.accelerator.rebellions.atom_plus.plugin import ATOMPlusPlugin
from ai.backend.accelerator.rebellions.common.atom_api import (
    ATOMAPI,
    ATOMDevicePCIInfo,
    ATOMDeviceStat,
    ATOMStat,
    ATOMStatMemory,
)
from ai.backend.accelerator.rebellions.common.plugin import AbstractATOMPlugin
from ai.backend.agent.stats import ContainerMeasurement, Measurement

CONTAINER_ID = "atom_plus_container"


def _device_stat(
    *,
    name: str,
    device: str,
    bus_id: str,
    mem_used: int,
    mem_total: int,
    util: int,
    sid: str | None = None,
    npu: int = 0,
) -> ATOMDeviceStat:
    return ATOMDeviceStat(
        group_id="0",
        npu=npu,
        name=name,
        sid=sid,
        uuid=f"uuid-{device}",
        device=device,
        pci=ATOMDevicePCIInfo(bus_id=bus_id, numa_node=0, link_speed="", link_width=""),
        temperature="40",
        memory=ATOMStatMemory(used=str(mem_used), total=str(mem_total)),
        util=str(util),
    )


class TestContainerMeasureIsolation:
    @pytest.fixture
    def stat_context(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture
    def host_stats(self) -> ATOMStat:
        # A host with one device of each ATOM variant; the atom-plus device (rbln2)
        # is the one mounted into the container under test.
        return ATOMStat(
            KMD_version="1.0",
            devices=[
                _device_stat(
                    name="RBLN-CA02",
                    device="rbln0",
                    bus_id="0000:01:00.0",
                    mem_used=100,
                    mem_total=1000,
                    util=10,
                ),
                _device_stat(
                    name="RBLN-CA25",
                    device="rbln1",
                    bus_id="0000:02:00.0",
                    mem_used=200,
                    mem_total=2000,
                    util=20,
                    sid="sid-max-0",
                    npu=1,
                ),
                _device_stat(
                    name="RBLN-CA12",
                    device="rbln2",
                    bus_id="0000:03:00.0",
                    mem_used=512,
                    mem_total=8000,
                    util=45,
                    npu=2,
                ),
            ],
        )

    @pytest.fixture
    def container_info(self) -> dict[str, Any]:
        return {
            "HostConfig": {
                "Devices": [
                    {
                        "PathOnHost": "/dev/rbln2",
                        "PathInContainer": "/dev/rbln0",
                        "CgroupPermissions": "rwm",
                    },
                ],
            },
        }

    @pytest.fixture
    def mock_docker(self, container_info: dict[str, Any]) -> AsyncMock:
        docker = AsyncMock()
        docker.__aenter__ = AsyncMock(return_value=docker)
        docker.__aexit__ = AsyncMock(return_value=False)
        docker.containers.get = AsyncMock(return_value=container_info)
        return docker

    @pytest.fixture
    def patched_env(
        self,
        host_stats: ATOMStat,
        mock_docker: AsyncMock,
    ) -> Iterator[None]:
        with (
            patch.object(ATOMAPI, "get_stats", AsyncMock(return_value=host_stats)),
            patch(
                "ai.backend.accelerator.rebellions.common.plugin.Docker",
                return_value=mock_docker,
            ),
        ):
            yield

    @pytest.fixture
    def plugin(self, request: pytest.FixtureRequest) -> AbstractATOMPlugin[Any]:
        plugin_cls: type[AbstractATOMPlugin[Any]] = request.param
        plugin = plugin_cls.__new__(plugin_cls)
        plugin.plugin_config = {}
        plugin.enabled = True
        plugin.device_mask = []
        plugin._rbln_stat_path = "/usr/bin/rbln-stat"
        plugin._all_devices = None
        return plugin

    @pytest.mark.parametrize(
        ("plugin", "expected_mem", "expected_util", "expected_devices"),
        [
            (ATOMPlugin, Decimal(0), Decimal(0), 0),
            (ATOMMaxPlugin, Decimal(0), Decimal(0), 0),
            (ATOMPlusPlugin, Decimal(512), Decimal(45), 1),
        ],
        indirect=["plugin"],
        ids=["atom", "atom-max", "atom-plus"],
    )
    async def test_reports_own_variant_only(
        self,
        plugin: AbstractATOMPlugin[Any],
        expected_mem: Decimal,
        expected_util: Decimal,
        expected_devices: int,
        stat_context: MagicMock,
        patched_env: None,
    ) -> None:
        """Container holds only the atom-plus device (rbln2). See container info fixture."""
        measures: list[ContainerMeasurement] = list(
            await plugin.gather_container_measures(stat_context, [CONTAINER_ID])
        )
        mem_measure, util_measure = measures

        mem: Measurement = mem_measure.per_container[CONTAINER_ID]
        util: Measurement = util_measure.per_container[CONTAINER_ID]
        assert mem.value == expected_mem
        assert util.value == expected_util
        assert util.capacity == Decimal(expected_devices * 100)
