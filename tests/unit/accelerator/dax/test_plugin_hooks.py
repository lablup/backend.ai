import json
from decimal import Decimal
from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock

import pytest
from aiodocker.exceptions import DockerError

from ai.backend.accelerator.dax.plugin import DAXPlugin
from ai.backend.agent.errors.resources import InvalidResourceArgument
from ai.backend.agent.resources import DeviceAllocation
from ai.backend.agent.stats import StatContext
from ai.backend.common.types import BinarySize, DeviceId, SlotName

from .conftest import (
    ALIGN,
    DEVICE_SIZE,
    FAKE_GID,
    FakeDocker,
    FakeStat,
    FakeSysfs,
    PluginFactory,
)

SLOT = SlotName("dax.device")
DEV_A = DeviceId("dax-0x1a2b")
DEV_B = DeviceId("dax-0x3c4d")
PATH_A = "/host/dev/dax0.0"
PATH_B = "/host/dev/dax1.0"
KERNEL_1 = "kernel-1"
KERNEL_2 = "kernel-2"


def _hwinfo_devices(metadata: dict[str, str]) -> dict[str, dict[str, Any]]:
    return {d["id"]: d for d in json.loads(metadata["devices"])}


@pytest.fixture
def two_devices(fake_sysfs: FakeSysfs) -> None:
    fake_sysfs.add_cxl_device("dax0.0", serials=("0x1a2b",))
    fake_sysfs.add_cxl_device("dax1.0", region="region1", serials=("0x3c4d",))


class TestGrantHooks:
    @pytest.fixture
    async def plugin(self, two_devices: None, plugin_factory: PluginFactory) -> DAXPlugin:
        return await plugin_factory()

    async def test_docker_args_mount_granted_devices(self, plugin: DAXPlugin) -> None:
        args = await plugin.generate_docker_args(MagicMock(), {SLOT: {DEV_A: Decimal(1)}})

        assert args["HostConfig"]["Devices"] == [
            {
                "PathOnHost": "/host/dev/dax0.0",
                "PathInContainer": "/dev/dax0.0",
                "CgroupPermissions": "rw",
            }
        ]
        env = dict(item.split("=", 1) for item in args["Env"])
        assert env["BACKENDAI_DAX_PATHS"] == "/dev/dax0.0"
        assert json.loads(env["BACKENDAI_DAX_DEVICES"]) == [
            {
                "id": DEV_A,
                "path": "/dev/dax0.0",
                "size": DEVICE_SIZE,
                "align": ALIGN,
                "numa_node": 1,
                "target_node": 2,
                "region": "region0",
                "serials": ["0x1a2b"],
            }
        ]

    async def test_resource_data_lists_granted_devices(self, plugin: DAXPlugin) -> None:
        data = await plugin.generate_resource_data({SLOT: {DEV_A: Decimal(1), DEV_B: Decimal(1)}})

        assert list(data) == ["DAX_DEVICES"]
        assert [d["id"] for d in json.loads(data["DAX_DEVICES"])] == [DEV_A, DEV_B]

    async def test_attached_devices(self, plugin: DAXPlugin) -> None:
        attached = await plugin.get_attached_devices({SLOT: {DEV_B: Decimal(1)}})

        assert attached == [
            {
                "device_id": DEV_B,
                "model_name": "device-DAX",
                "data": {"mem": BinarySize(DEVICE_SIZE)},
            }
        ]

    async def test_additional_gids(self, plugin: DAXPlugin) -> None:
        assert plugin.get_additional_gids() == [FAKE_GID]

    async def test_grant_sets_last_granted_at_in_hwinfo(self, plugin: DAXPlugin) -> None:
        await plugin.generate_docker_args(MagicMock(), {SLOT: {DEV_A: Decimal(1)}})

        hwinfo = await plugin.get_node_hwinfo()

        assert hwinfo["status"] == "healthy"
        metadata = hwinfo["metadata"]
        assert metadata["max_holders"] == "1"
        assert metadata["agent_started_at"]
        assert metadata["config_path"].endswith("dax-accelerator.toml")
        assert "invalid_config" not in metadata
        devices = {d["id"]: d for d in json.loads(metadata["devices"])}
        assert devices[DEV_A]["last_granted_at"] is not None
        assert devices[DEV_B]["last_granted_at"] is None
        assert devices[DEV_A]["excluded_reason"] is None
        assert devices[DEV_A]["driver"] == "device_dax"

    async def test_repeated_grants_count_in_hwinfo(self, plugin: DAXPlugin) -> None:
        await plugin.generate_docker_args(MagicMock(), {SLOT: {DEV_A: Decimal(1)}})
        await plugin.generate_docker_args(MagicMock(), {SLOT: {DEV_A: Decimal(1)}})

        hwinfo = await plugin.get_node_hwinfo()

        devices = {d["id"]: d for d in json.loads(hwinfo["metadata"]["devices"])}
        assert devices[DEV_A]["grant_count"] == 2
        assert devices[DEV_A]["last_granted_at"] is not None
        assert devices[DEV_B]["grant_count"] == 0
        assert devices[DEV_B]["last_granted_at"] is None

    async def test_ungranted_foreign_id_is_rejected(self, plugin: DAXPlugin) -> None:
        with pytest.raises(InvalidResourceArgument):
            await plugin.generate_docker_args(
                MagicMock(), {SLOT: {DeviceId("dax-0xdead"): Decimal(1)}}
            )


class TestCapacity:
    async def test_slots_are_devices_times_max_holders(
        self, two_devices: None, plugin_factory: PluginFactory
    ) -> None:
        plugin = await plugin_factory("max_holders = 2")

        assert await plugin.available_slots() == {SLOT: Decimal(4)}
        assert {d.device_id for d in await plugin.list_devices()} == {DEV_A, DEV_B}
        alloc_map = await plugin.create_alloc_map()
        assert {dev: info.amount for dev, info in alloc_map.device_slots.items()} == {
            DEV_A: Decimal(2),
            DEV_B: Decimal(2),
        }


class TestHookEdges:
    @pytest.fixture
    async def plugin(self, two_devices: None, plugin_factory: PluginFactory) -> DAXPlugin:
        return await plugin_factory()

    @pytest.mark.parametrize(
        "device_alloc",
        [
            pytest.param({}, id="empty"),
            pytest.param({SLOT: {DEV_A: Decimal(0)}}, id="zero"),
        ],
    )
    async def test_empty_allocation_yields_nothing(
        self, plugin: DAXPlugin, device_alloc: DeviceAllocation
    ) -> None:
        assert await plugin.generate_docker_args(MagicMock(), device_alloc) == {}
        assert await plugin.generate_resource_data(device_alloc) == {}
        assert list(await plugin.get_attached_devices(device_alloc)) == []

    @pytest.mark.parametrize(
        "device_alloc",
        [
            pytest.param({}, id="empty"),
            pytest.param({SLOT: {DEV_A: Decimal(0)}}, id="zero"),
        ],
    )
    async def test_empty_allocation_keeps_grant_counts(
        self, plugin: DAXPlugin, device_alloc: DeviceAllocation
    ) -> None:
        await plugin.generate_docker_args(MagicMock(), {SLOT: {DEV_A: Decimal(1)}})

        await plugin.generate_docker_args(MagicMock(), device_alloc)

        hwinfo = await plugin.get_node_hwinfo()
        counts = {d["id"]: d["grant_count"] for d in json.loads(hwinfo["metadata"]["devices"])}
        assert counts == {DEV_A: 1, DEV_B: 0}

    async def test_mock_uses_path_on_host(
        self, fake_sysfs: FakeSysfs, fake_stat: FakeStat, plugin_factory: PluginFactory
    ) -> None:
        fake_sysfs.add_cxl_device("dax0.0")
        fake_stat.missing.add("dax0.0")
        plugin = await plugin_factory('mock = true\n[path_on_host]\n"dax0.0" = "/tmp/fake-dax"')

        args = await plugin.generate_docker_args(MagicMock(), {SLOT: {DEV_A: Decimal(1)}})

        assert args["HostConfig"]["Devices"][0]["PathOnHost"] == "/tmp/fake-dax"
        assert args["HostConfig"]["Devices"][0]["PathInContainer"] == "/dev/dax0.0"

    async def test_measures_are_empty(self, plugin: DAXPlugin) -> None:
        ctx = MagicMock(spec=StatContext)

        assert list(await plugin.gather_node_measures(ctx)) == []
        assert list(await plugin.gather_container_measures(ctx, ["c1"])) == []
        assert list(await plugin.gather_process_measures(ctx, {1: "c1"})) == []


class TestHwinfoStatus:
    async def test_all_excluded_is_degraded(
        self, two_devices: None, fake_stat: FakeStat, plugin_factory: PluginFactory
    ) -> None:
        fake_stat.missing.update({"dax0.0", "dax1.0"})
        plugin = await plugin_factory()

        hwinfo = await plugin.get_node_hwinfo()

        assert hwinfo["status"] == "degraded"
        reasons = {
            d["name"]: d["excluded_reason"] for d in json.loads(hwinfo["metadata"]["devices"])
        }
        assert reasons == {"dax0.0": "node_missing", "dax1.0": "node_missing"}

    async def test_no_device_is_unavailable(self, plugin_factory: PluginFactory) -> None:
        plugin = await plugin_factory()

        hwinfo = await plugin.get_node_hwinfo()

        assert hwinfo["status"] == "unavailable"
        assert json.loads(hwinfo["metadata"]["devices"]) == []


class TestHwinfoHolders:
    @pytest.fixture
    async def plugin(self, two_devices: None, plugin_factory: PluginFactory) -> DAXPlugin:
        return await plugin_factory()

    @pytest.fixture
    def holder_on_a(self, fake_docker: FakeDocker) -> None:
        fake_docker.add_container("c1", kernel_id=KERNEL_1, devices=[PATH_A])

    async def test_running_kernel_container_is_listed(
        self, holder_on_a: None, plugin: DAXPlugin
    ) -> None:
        metadata = (await plugin.get_node_hwinfo())["metadata"]

        devices = _hwinfo_devices(metadata)
        assert devices[DEV_A]["holders"] == [{"kernel_id": KERNEL_1, "container_id": "c1"}]
        assert devices[DEV_B]["holders"] == []
        assert metadata["holder_scan_error"] == ""

    async def test_no_kernel_containers_gives_empty_holders(self, plugin: DAXPlugin) -> None:
        metadata = (await plugin.get_node_hwinfo())["metadata"]

        assert {d: v["holders"] for d, v in _hwinfo_devices(metadata).items()} == {
            DEV_A: [],
            DEV_B: [],
        }
        assert metadata["holder_scan_error"] == ""

    @pytest.mark.parametrize(
        ("kernel_id", "devices", "running"),
        [
            pytest.param(KERNEL_1, [PATH_B], True, id="other-dax-device"),
            pytest.param(KERNEL_1, ["/dev/fuse"], True, id="non-dax-kernel"),
            pytest.param(None, [PATH_A], True, id="not-a-kernel"),
            pytest.param(KERNEL_1, [PATH_A], False, id="not-running"),
        ],
    )
    async def test_non_holder_is_not_listed(
        self,
        fake_docker: FakeDocker,
        plugin: DAXPlugin,
        kernel_id: str | None,
        devices: list[str],
        running: bool,
    ) -> None:
        fake_docker.add_container("c9", kernel_id=kernel_id, devices=devices, running=running)

        metadata = (await plugin.get_node_hwinfo())["metadata"]

        assert _hwinfo_devices(metadata)[DEV_A]["holders"] == []

    async def test_max_holders_two_lists_both(
        self, two_devices: None, fake_docker: FakeDocker, plugin_factory: PluginFactory
    ) -> None:
        fake_docker.add_container("c1", kernel_id=KERNEL_1, devices=[PATH_A])
        fake_docker.add_container("c2", kernel_id=KERNEL_2, devices=[PATH_A])
        plugin = await plugin_factory("max_holders = 2")

        metadata = (await plugin.get_node_hwinfo())["metadata"]

        assert _hwinfo_devices(metadata)[DEV_A]["holders"] == [
            {"kernel_id": KERNEL_1, "container_id": "c1"},
            {"kernel_id": KERNEL_2, "container_id": "c2"},
        ]

    async def test_list_failure_is_scan_error(
        self, holder_on_a: None, fake_docker: FakeDocker, plugin: DAXPlugin
    ) -> None:
        await plugin.generate_docker_args(MagicMock(), {SLOT: {DEV_A: Decimal(1)}})
        fake_docker.list_error = DockerError(HTTPStatus.INTERNAL_SERVER_ERROR, "daemon down")

        hwinfo = await plugin.get_node_hwinfo()

        metadata = hwinfo["metadata"]
        devices = _hwinfo_devices(metadata)
        assert devices[DEV_A]["holders"] is None
        assert devices[DEV_B]["holders"] is None
        assert "daemon down" in metadata["holder_scan_error"]
        assert hwinfo["status"] == "healthy"
        assert metadata["max_holders"] == "1"
        assert devices[DEV_A]["grant_count"] == 1
        assert devices[DEV_A]["driver"] == "device_dax"

    async def test_container_removed_before_inspect_is_skipped(
        self, holder_on_a: None, fake_docker: FakeDocker, plugin: DAXPlugin
    ) -> None:
        fake_docker.add_container("c2", kernel_id=KERNEL_2, devices=[PATH_A])
        fake_docker.remove_before_inspect("c2")

        metadata = (await plugin.get_node_hwinfo())["metadata"]

        assert _hwinfo_devices(metadata)[DEV_A]["holders"] == [
            {"kernel_id": KERNEL_1, "container_id": "c1"}
        ]
        assert metadata["holder_scan_error"] == ""

    async def test_other_inspect_error_is_scan_error(
        self, holder_on_a: None, fake_docker: FakeDocker, plugin: DAXPlugin
    ) -> None:
        fake_docker.inspect_errors["c1"] = DockerError(
            HTTPStatus.INTERNAL_SERVER_ERROR, "inspect failed"
        )

        metadata = (await plugin.get_node_hwinfo())["metadata"]

        assert _hwinfo_devices(metadata)[DEV_A]["holders"] is None
        assert "inspect failed" in metadata["holder_scan_error"]

    async def test_scan_timeout_is_scan_error(
        self,
        two_devices: None,
        holder_on_a: None,
        fake_docker: FakeDocker,
        plugin_factory: PluginFactory,
    ) -> None:
        fake_docker.list_delay = 1.0
        plugin = await plugin_factory(holder_scan_timeout=0.01)

        metadata = (await plugin.get_node_hwinfo())["metadata"]

        assert {d: v["holders"] for d, v in _hwinfo_devices(metadata).items()} == {
            DEV_A: None,
            DEV_B: None,
        }
        assert "timed out" in metadata["holder_scan_error"]

    @pytest.mark.parametrize(
        "devices",
        [pytest.param(None, id="null"), pytest.param([], id="empty")],
    )
    async def test_container_without_devices_holds_nothing(
        self, fake_docker: FakeDocker, plugin: DAXPlugin, devices: list[str] | None
    ) -> None:
        fake_docker.add_container("c1", kernel_id=KERNEL_1, devices=devices)

        metadata = (await plugin.get_node_hwinfo())["metadata"]

        assert _hwinfo_devices(metadata)[DEV_A]["holders"] == []
        assert metadata["holder_scan_error"] == ""

    @pytest.mark.parametrize(
        ("extra_toml", "path_on_host"),
        [
            pytest.param(
                '[path_on_host]\n"dax0.0" = "/tmp/fake-dax"', "/tmp/fake-dax", id="mapped"
            ),
            pytest.param("", PATH_A, id="dev-root"),
        ],
    )
    async def test_mock_path_on_host_matches(
        self,
        fake_sysfs: FakeSysfs,
        fake_stat: FakeStat,
        fake_docker: FakeDocker,
        plugin_factory: PluginFactory,
        extra_toml: str,
        path_on_host: str,
    ) -> None:
        fake_sysfs.add_cxl_device("dax0.0")
        fake_stat.missing.add("dax0.0")
        fake_docker.add_container("c1", kernel_id=KERNEL_1, devices=[path_on_host])
        plugin = await plugin_factory(f"mock = true\n{extra_toml}")

        metadata = (await plugin.get_node_hwinfo())["metadata"]

        assert _hwinfo_devices(metadata)[DEV_A]["holders"] == [
            {"kernel_id": KERNEL_1, "container_id": "c1"}
        ]

    async def test_grant_fields_unchanged_with_holders(
        self, holder_on_a: None, plugin: DAXPlugin
    ) -> None:
        await plugin.generate_docker_args(MagicMock(), {SLOT: {DEV_A: Decimal(1)}})

        metadata = (await plugin.get_node_hwinfo())["metadata"]

        devices = _hwinfo_devices(metadata)
        assert metadata["agent_started_at"]
        assert devices[DEV_A]["grant_count"] == 1
        assert devices[DEV_A]["last_granted_at"] is not None
        assert devices[DEV_B]["grant_count"] == 0
        assert devices[DEV_B]["last_granted_at"] is None
        assert len(devices[DEV_A]["holders"]) == 1
