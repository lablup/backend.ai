"""
Unit tests for the AWS Neuron accelerator plugin.

The ``neuron-ls --json-output`` payload below is verbatim real output captured
from a ``trn1.2xlarge`` instance (1 Trainium device / 2 NeuronCores, driver
``aws-neuronx-dkms 2.26.5.0``, tools ``aws-neuronx-tools 2.28.23.0``).  Do not
"tidy" the value shapes: ``neuron_device`` really is an int while ``numa_node``
really is a string, ``connected_to`` really is null on a single-device
instance, and ``memory_size`` really is bare bytes.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from ai.backend.accelerator.neuron.neuron_api import (
    NeuronAPI,
    NeuronCoreStats,
    NeuronDeviceInfo,
    NeuronDriverUnavailableError,
    NeuronToolError,
)
from ai.backend.accelerator.neuron.plugin import NeuronPlugin
from ai.backend.common.types import DeviceId, MetricKey, SlotName

# Captured from `neuron-ls --json-output` on trn1.2xlarge.
TRN1_2XLARGE_NEURON_LS_JSON = """
[
    {
        "neuron_device": 0,
        "bdf": "0000:00:1e.0",
        "cpu_affinity": "0-7",
        "numa_node": "-1",
        "connected_to": null,
        "nc_count": 2,
        "memory_size": 34359738368,
        "neuroncore_ids": [
            0,
            1
        ],
        "neuron_processes": []
    }
]
"""

# Synthesized two-device shape for renumbering coverage.  We only ever had a
# single-device instance, so the *values* here are extrapolated: the device
# indices are non-contiguous on purpose to prove the container-side renumbering
# does not simply echo the host index.
TWO_DEVICE_NEURON_LS_JSON = """
[
    {
        "neuron_device": 0,
        "bdf": "0000:00:1e.0",
        "cpu_affinity": "0-7",
        "numa_node": "0",
        "connected_to": [3],
        "nc_count": 2,
        "memory_size": 34359738368,
        "neuroncore_ids": [0, 1],
        "neuron_processes": []
    },
    {
        "neuron_device": 3,
        "bdf": "0000:00:1f.0",
        "cpu_affinity": "8-15",
        "numa_node": "1",
        "connected_to": [0],
        "nc_count": 2,
        "memory_size": 34359738368,
        "neuroncore_ids": [6, 7],
        "neuron_processes": []
    }
]
"""

GIB = 1024**3

# The plugin ignores these arguments; typed as Any to keep the call sites readable.
NO_DOCKER: Any = None
NO_CTX: Any = None


def _parse(raw: str) -> list[NeuronDeviceInfo]:
    return [NeuronDeviceInfo.from_json_obj(entry) for entry in json.loads(raw)]


@pytest.fixture
def stub_sysfs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the plugin off the test host's real /sys and /dev."""
    stubs = {
        "read_device_serial": "9ff5434815c8bd80",
        "read_device_model_name": "Trainium1",
        "read_device_arch_type": "NDv2",
    }
    for name, value in stubs.items():
        monkeypatch.setattr(NeuronAPI, name, classmethod(lambda cls, index, _v=value: _v))


async def _make_plugin(
    monkeypatch: pytest.MonkeyPatch,
    raw_json: str,
    *,
    plugin_config: dict[str, Any] | None = None,
) -> NeuronPlugin:
    """Build an initialized plugin whose discovery returns the given payload."""
    infos = _parse(raw_json)

    async def fake_list_devices(cls: Any, exec_path: str) -> list[NeuronDeviceInfo]:
        return infos

    monkeypatch.setattr(NeuronAPI, "list_devices", classmethod(fake_list_devices))
    monkeypatch.setattr(
        "ai.backend.accelerator.neuron.plugin.resolve_neuron_ls_path",
        lambda configured=None: "/opt/aws/neuron/bin/neuron-ls",
    )
    plugin = NeuronPlugin(plugin_config or {}, {})
    await plugin.init()
    return plugin


class TestNeuronLsParsing:
    def test_parses_the_real_captured_payload(self) -> None:
        infos = _parse(TRN1_2XLARGE_NEURON_LS_JSON)
        assert len(infos) == 1
        info = infos[0]
        assert info.neuron_device == 0
        assert info.bdf == "0000:00:1e.0"
        assert info.nc_count == 2
        assert info.neuroncore_ids == (0, 1)
        # `connected_to` is null on a single-device instance.
        assert info.connected_to is None

    def test_numa_node_arrives_as_a_string(self) -> None:
        (info,) = _parse(TRN1_2XLARGE_NEURON_LS_JSON)
        # The JSON value is the *string* "-1"; parsing must not crash and must
        # yield an int.
        assert isinstance(info.numa_node, int)
        assert info.numa_node == -1

    def test_memory_size_is_bare_bytes(self) -> None:
        (info,) = _parse(TRN1_2XLARGE_NEURON_LS_JSON)
        # 34359738368 == exactly 32 GiB, as bytes -- not "32 GB" to be parsed.
        assert info.memory_size == 32 * GIB
        assert info.memory_size_per_core == 16 * GIB

    def test_rejects_a_non_array_payload(self) -> None:
        with pytest.raises(NeuronToolError):
            NeuronDeviceInfo.from_json_obj("not an object")

    def test_reports_a_missing_key(self) -> None:
        with pytest.raises(NeuronToolError, match="nc_count"):
            NeuronDeviceInfo.from_json_obj({"neuron_device": 0, "bdf": "x", "numa_node": "0"})


class TestSubprocessWrapper:
    """`neuron-ls` invocation, including the driver-absent (degraded) host."""

    @staticmethod
    def _fake_exec(monkeypatch: pytest.MonkeyPatch, stdout: bytes, stderr: bytes, rc: int) -> None:
        class FakeProc:
            returncode = rc

            async def communicate(self) -> tuple[bytes, bytes]:
                return stdout, stderr

        async def fake_create(*args: Any, **kwargs: Any) -> FakeProc:
            return FakeProc()

        monkeypatch.setattr(
            "ai.backend.accelerator.neuron.neuron_api.asyncio.create_subprocess_exec",
            fake_create,
        )

    async def test_parses_a_healthy_invocation(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._fake_exec(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON.encode(), b"", 0)
        infos = await NeuronAPI.list_devices("/opt/aws/neuron/bin/neuron-ls")
        assert len(infos) == 1
        assert infos[0].nc_count == 2

    async def test_empty_stdout_with_nonzero_exit_means_no_driver(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Real degraded-host behaviour: stdout empty and clean, one logfmt line
        # on stderr, exit 1.
        stderr = (
            b'time="2026-09-12T02:42:06Z" level=fatal '
            b'msg="Failed to load MLA system information" '
            b'error="failed to discover Neuron devices"\n'
        )
        self._fake_exec(monkeypatch, b"", stderr, 1)
        with pytest.raises(NeuronDriverUnavailableError):
            await NeuronAPI.list_devices("/opt/aws/neuron/bin/neuron-ls")

    async def test_unparseable_output_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._fake_exec(monkeypatch, b"not json", b"", 0)
        with pytest.raises(NeuronToolError):
            await NeuronAPI.list_devices("/opt/aws/neuron/bin/neuron-ls")


class TestDiscovery:
    async def test_one_device_with_two_cores_yields_two_core_devices(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        devices = await plugin.list_devices()
        assert len(devices) == 2
        assert [d.device_id for d in devices] == [DeviceId("0"), DeviceId("1")]
        assert [d.core_index for d in devices] == [0, 1]
        assert {d.neuron_device_index for d in devices} == {0}

    async def test_memory_size_splits_per_core_and_is_bytes(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        devices = await plugin.list_devices()
        assert all(d.memory_size == 16 * GIB for d in devices)
        assert sum(d.memory_size for d in devices) == 32 * GIB

    async def test_numa_node_minus_one_does_not_crash_and_clamps_to_zero(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        devices = await plugin.list_devices()
        assert all(d.numa_node == 0 for d in devices)

    async def test_hw_location_comes_from_the_bdf(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        devices = await plugin.list_devices()
        assert all(d.hw_location == "0000:00:1e.0" for d in devices)

    async def test_device_identity_is_metadata_not_the_key(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        devices = await plugin.list_devices()
        assert all(d.serial == "9ff5434815c8bd80" for d in devices)
        # ... but the allocation key is the core, so the two cores are distinct.
        assert len({d.device_id for d in devices}) == 2

    async def test_available_slots_reports_the_core_count(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        assert await plugin.available_slots() == {SlotName("neuron.core"): Decimal(2)}

    async def test_alloc_map_has_one_unit_per_core(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        alloc_map = await plugin.create_alloc_map()
        assert set(alloc_map.device_slots) == {DeviceId("0"), DeviceId("1")}
        assert all(
            info.slot_name == SlotName("neuron.core") and info.amount == Decimal(1)
            for info in alloc_map.device_slots.values()
        )

    async def test_device_mask_hides_cores(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(
            monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON, plugin_config={"device_mask": "1"}
        )
        devices = await plugin.list_devices()
        assert [d.device_id for d in devices] == [DeviceId("0")]


class TestAbsenceHandling:
    async def test_missing_cli_disables_the_plugin_without_raising(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "ai.backend.accelerator.neuron.plugin.resolve_neuron_ls_path",
            lambda configured=None: None,
        )

        async def explode(cls: Any, exec_path: str) -> list[NeuronDeviceInfo]:
            raise AssertionError("discovery must not be attempted without a CLI")

        monkeypatch.setattr(NeuronAPI, "list_devices", classmethod(explode))

        plugin = NeuronPlugin({}, {})
        await plugin.init()  # must not raise

        assert plugin.enabled is False
        assert await plugin.list_devices() == []
        assert await plugin.available_slots() == {SlotName("neuron.core"): Decimal(0)}

    async def test_degraded_host_disables_the_plugin_without_raising(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "ai.backend.accelerator.neuron.plugin.resolve_neuron_ls_path",
            lambda configured=None: "/opt/aws/neuron/bin/neuron-ls",
        )

        async def no_driver(cls: Any, exec_path: str) -> list[NeuronDeviceInfo]:
            raise NeuronDriverUnavailableError("no neuron device found")

        monkeypatch.setattr(NeuronAPI, "list_devices", classmethod(no_driver))

        plugin = NeuronPlugin({}, {})
        await plugin.init()  # must not raise

        assert plugin.enabled is False

    async def test_gather_node_measures_is_safe_while_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "ai.backend.accelerator.neuron.plugin.resolve_neuron_ls_path",
            lambda configured=None: None,
        )
        plugin = NeuronPlugin({}, {})
        await plugin.init()
        measures = await plugin.gather_node_measures(NO_CTX)
        assert [m.key for m in measures] == ["neuron_mem", "neuron_host_mem"]
        assert all(m.per_device == {} for m in measures)


class TestNodeMeasures:
    async def test_reports_per_core_memory_from_sysfs(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)

        # Values shaped like the captured sysfs leaves: device_mem idle at 0,
        # host_mem populated with no workload attached.
        stats = {
            (0, 0): NeuronCoreStats(
                device_mem_present=8 * GIB,
                device_mem_peak=9 * GIB,
                host_mem_present=4096,
                host_mem_peak=4530176,
            ),
            (0, 1): NeuronCoreStats(
                device_mem_present=0,
                device_mem_peak=0,
                host_mem_present=4096,
                host_mem_peak=266240,
            ),
        }

        async def fake_batch(cls: Any, coords: Any) -> dict[tuple[int, int], NeuronCoreStats]:
            return {coord: stats[coord] for coord in coords}

        monkeypatch.setattr(NeuronAPI, "read_core_stats_batch", classmethod(fake_batch))

        measures = {m.key: m for m in await plugin.gather_node_measures(NO_CTX)}

        mem = measures[MetricKey("neuron_mem")]
        assert mem.unit_hint == "bytes"
        assert mem.per_device[DeviceId("0")].value == Decimal(8 * GIB)
        # Capacity is the per-core split of the neuron-ls device capacity, NOT
        # the sysfs `total` leaf (which is a cumulative counter reading 0 here).
        assert mem.per_device[DeviceId("0")].capacity == Decimal(16 * GIB)
        assert mem.per_node.value == Decimal(8 * GIB)
        assert mem.per_node.capacity == Decimal(32 * GIB)

        host = measures[MetricKey("neuron_host_mem")]
        assert host.per_device[DeviceId("1")].value == Decimal(4096)
        assert host.per_node.value == Decimal(8192)

    def test_metric_keys_contain_no_dots(self) -> None:
        # The agent requires stat keys without dots, so `neuron.core` cannot be
        # reused verbatim as a metric key.
        for key in ("neuron_mem", "neuron_host_mem"):
            assert "." not in key


class TestContainerPlumbing:
    @staticmethod
    def _alloc(*core_ids: str) -> dict[SlotName, dict[DeviceId, Decimal]]:
        return {SlotName("neuron.core"): {DeviceId(c): Decimal(1) for c in core_ids}}

    @pytest.fixture(autouse=True)
    def _device_nodes_exist(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "ai.backend.accelerator.neuron.plugin._device_node_exists",
            lambda path: True,
        )

    async def test_mounts_and_renumbers_device_nodes(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TWO_DEVICE_NEURON_LS_JSON)
        # One core from host device 0 and one from host device 3.
        args = await plugin.generate_docker_args(NO_DOCKER, self._alloc("0", "6"))

        devices = args["HostConfig"]["Devices"]
        assert [(d["PathOnHost"], d["PathInContainer"]) for d in devices] == [
            ("/dev/neuron0", "/dev/neuron0"),
            ("/dev/neuron3", "/dev/neuron1"),
        ]
        assert all(d["CgroupPermissions"] == "rwm" for d in devices)

    async def test_sets_the_pinned_memory_options(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        args = await plugin.generate_docker_args(NO_DOCKER, self._alloc("0"))
        host_config = args["HostConfig"]
        assert host_config["CapAdd"] == ["IPC_LOCK"]
        assert host_config["IpcMode"] == "host"
        assert host_config["Ulimits"] == [{"Name": "memlock", "Hard": -1, "Soft": -1}]

    async def test_visible_cores_are_container_local(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TWO_DEVICE_NEURON_LS_JSON)
        # Global core 1 lives on host device 0 (local index 1); global core 7
        # lives on host device 3, which is renumbered to container device 1, so
        # its container-local core index is 1 * nc_count + 1 == 3.
        args = await plugin.generate_docker_args(NO_DOCKER, self._alloc("1", "7"))
        assert args["Env"] == ["NEURON_RT_VISIBLE_CORES=1,3"]

    async def test_allocating_one_core_still_mounts_the_whole_device(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        args = await plugin.generate_docker_args(NO_DOCKER, self._alloc("0"))
        # A device node carries all of its cores, so exactly one node is mounted
        # even though only one of its two cores was allocated ...
        assert len(args["HostConfig"]["Devices"]) == 1
        # ... and only the allocated core is made visible to the runtime.
        assert args["Env"] == ["NEURON_RT_VISIBLE_CORES=0"]

    async def test_no_allocation_yields_no_docker_args(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        assert await plugin.generate_docker_args(NO_DOCKER, self._alloc()) == {}

    async def test_missing_device_node_is_skipped_not_fatal(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)

        monkeypatch.setattr(
            "ai.backend.accelerator.neuron.plugin._device_node_exists",
            lambda path: False,
        )
        args = await plugin.generate_docker_args(NO_DOCKER, self._alloc("0"))
        assert args["HostConfig"]["Devices"] == []

    async def test_resource_data_maps_local_to_global_core_ids(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TWO_DEVICE_NEURON_LS_JSON)
        data = await plugin.generate_resource_data(self._alloc("1", "6"))
        assert data == {"NEURON_GLOBAL_CORE_IDS": "0:1,1:6"}

    async def test_attached_devices_report_the_per_core_memory(
        self, monkeypatch: pytest.MonkeyPatch, stub_sysfs: None
    ) -> None:
        plugin = await _make_plugin(monkeypatch, TRN1_2XLARGE_NEURON_LS_JSON)
        attached = await plugin.get_attached_devices(self._alloc("1"))
        assert len(attached) == 1
        assert attached[0]["device_id"] == DeviceId("1")
        assert int(attached[0]["data"]["mem"]) == 16 * GIB


class TestMetadata:
    def test_slot_name_is_the_core(self) -> None:
        assert NeuronPlugin.slot_types == ((SlotName("neuron.core"), "count"),)
        assert NeuronPlugin.exclusive_slot_types == {"neuron.core"}

    def test_metadata_slot_name_matches_the_declared_slot(self) -> None:
        metadata = NeuronPlugin({}, {}).get_metadata()
        assert metadata["slot_name"] == str(NeuronPlugin.slot_types[0][0])

    def test_declared_icon_exists_in_the_repo(self) -> None:
        # No `npu.svg` exists despite other plugins declaring `display_icon:
        # "npu"`; only ship an icon name that is actually present.
        icon = NeuronPlugin({}, {}).get_metadata()["display_icon"]
        icons_dir = Path(__file__).parents[4] / "src/ai/backend/web/static/resources/icons"
        if not icons_dir.is_dir():
            pytest.skip("icon assets are not part of this test's sandbox")
        assert list(icons_dir.glob(f"{icon}.*")), f"no icon asset for {icon!r}"
