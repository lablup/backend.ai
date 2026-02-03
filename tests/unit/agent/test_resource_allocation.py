"""
Unit tests for ResourcePartitioner and ResourceAllocator.

This file is organized into two main sections:
1. ResourcePartitioner unit tests - Direct tests of partitioning logic
2. ResourceAllocator integration tests - End-to-end tests through the allocator
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from ai.backend.agent.alloc_map import (
    AbstractAllocMap,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    FractionAllocMap,
)
from ai.backend.agent.config.unified import (
    AgentUnifiedConfig,
    ResourceAllocationMode,
)
from ai.backend.agent.errors.resources import InvalidResourceConfigError
from ai.backend.agent.resources import (
    AbstractComputeDevice,
    AbstractComputePlugin,
    DevicePartition,
    GlobalDeviceInfo,
    ResourceAllocator,
    ResourcePartitioner,
    SlotPartition,
    _natural_sort_key,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import (
    AgentId,
    BinarySize,
    DeviceId,
    DeviceName,
    SlotName,
    SlotTypes,
)

# =============================================================================
# Test Helpers
# =============================================================================


def create_test_config(
    *,
    allocation_mode: ResourceAllocationMode,
    reserved_cpu: int = 0,
    reserved_mem: str = "0",
    reserved_disk: str = "0",
    allocated_cpu: int | None = None,
    allocated_mem: str | None = None,
    allocated_devices: Mapping[SlotName, Decimal] | None = None,
    num_agents: int = 1,
) -> AgentUnifiedConfig:
    """Helper to create AgentUnifiedConfig for testing."""
    base_config: dict[str, Any] = {
        "agent": {
            "id": "agent1",
            "region": "local",
            "scaling_group": "default",
            "backend": "dummy",
            "rpc_listen_addr": "127.0.0.1:6001",
        },
        "container": {
            "scratch_type": "hostdir",
            "stats_type": "docker",
        },
        "resource": {
            "reserved_cpu": reserved_cpu,
            "reserved_mem": BinarySize.finite_from_str(reserved_mem),
            "reserved_disk": BinarySize.finite_from_str(reserved_disk),
            "allocation_mode": allocation_mode,
        },
        "etcd": {
            "addr": "127.0.0.1:2379",
            "namespace": "test",
        },
    }

    # Add manual allocation fields if provided
    if allocated_cpu is not None or allocated_mem is not None or allocated_devices is not None:
        base_config["resource"]["allocations"] = {}
        if allocated_cpu is not None:
            base_config["resource"]["allocations"]["cpu"] = allocated_cpu
        if allocated_mem is not None:
            base_config["resource"]["allocations"]["mem"] = BinarySize.finite_from_str(
                allocated_mem
            )
        if allocated_devices is not None:
            base_config["resource"]["allocations"]["devices"] = allocated_devices

    # Add multiple agents if requested
    if num_agents > 1:
        agents_list = []
        for i in range(num_agents):
            agent_override: dict[str, Any] = {
                "agent": {"id": f"agent{i + 1}"},
            }
            # In MANUAL mode, each agent needs allocation config
            if allocation_mode == ResourceAllocationMode.MANUAL:
                agent_override["resource"] = {
                    "cpu": allocated_cpu,
                    "mem": BinarySize.finite_from_str(allocated_mem) if allocated_mem else None,
                }
                if allocated_devices:
                    agent_override["resource"]["devices"] = allocated_devices
            agents_list.append(agent_override)
        base_config["agents"] = agents_list

    return AgentUnifiedConfig.model_validate(base_config)


def create_fraction_alloc_map(
    device_slots: Mapping[DeviceId, tuple[SlotName, Decimal]],
) -> FractionAllocMap:
    """Helper to create a FractionAllocMap."""
    slots = {
        dev_id: DeviceSlotInfo(
            slot_type=SlotTypes.BYTES,
            slot_name=slot_name,
            amount=amount,
        )
        for dev_id, (slot_name, amount) in device_slots.items()
    }
    return FractionAllocMap(device_slots=slots, exclusive_slot_types=set())


def create_discrete_alloc_map(
    device_slots: Mapping[DeviceId, tuple[SlotName, Decimal]],
) -> DiscretePropertyAllocMap:
    """Helper to create a DiscretePropertyAllocMap."""
    slots = {
        dev_id: DeviceSlotInfo(
            slot_type=SlotTypes.COUNT,
            slot_name=slot_name,
            amount=amount,
        )
        for dev_id, (slot_name, amount) in device_slots.items()
    }
    return DiscretePropertyAllocMap(device_slots=slots, exclusive_slot_types=set())


def create_mock_plugin(
    alloc_map: AbstractAllocMap,
    slot_types: Sequence[tuple[SlotName, SlotTypes]] | None = None,
) -> AbstractComputePlugin:
    """Helper to create a mock compute plugin."""
    mock_plugin: AbstractComputePlugin = Mock(spec=AbstractComputePlugin)
    mock_plugin.get_metadata.return_value = {}  # type: ignore[attr-defined]

    # Create mock devices for each device_id in the alloc_map
    mock_devices: list[AbstractComputeDevice] = []
    for dev_id in alloc_map.device_slots.keys():
        mock_device: AbstractComputeDevice = Mock(spec=AbstractComputeDevice)
        mock_device.device_id = dev_id
        mock_devices.append(mock_device)

    # Create a fresh alloc_map for each call
    async def _create_alloc_map(original_map: AbstractAllocMap = alloc_map) -> AbstractAllocMap:
        if isinstance(original_map, FractionAllocMap):
            return create_fraction_alloc_map({
                dev_id: (slot.slot_name, slot.amount)
                for dev_id, slot in original_map.device_slots.items()
            })
        if isinstance(original_map, DiscretePropertyAllocMap):
            return create_discrete_alloc_map({
                dev_id: (slot.slot_name, slot.amount)
                for dev_id, slot in original_map.device_slots.items()
            })
        raise NotImplementedError(f"Unsupported alloc_map type: {type(original_map)}")

    # Calculate available slots from the alloc_map
    available_slots: dict[SlotName, Decimal] = {}
    for slot_info in alloc_map.device_slots.values():
        if slot_info.slot_name not in available_slots:
            available_slots[slot_info.slot_name] = Decimal("0")
        available_slots[slot_info.slot_name] += slot_info.amount

    # Extract slot_types from the alloc_map if not provided
    if slot_types is None:
        slot_types_set: set[tuple[SlotName, SlotTypes]] = set()
        for slot_info in alloc_map.device_slots.values():
            slot_types_set.add((slot_info.slot_name, slot_info.slot_type))
        slot_types = list(slot_types_set)

    mock_plugin.slot_types = slot_types
    mock_plugin.create_alloc_map = _create_alloc_map  # type: ignore[method-assign]
    mock_plugin.list_devices = AsyncMock(return_value=mock_devices)  # type: ignore[method-assign]
    mock_plugin.available_slots = AsyncMock(return_value=available_slots)  # type: ignore[method-assign]
    mock_plugin.cleanup = AsyncMock(return_value=None)  # type: ignore[method-assign]

    return mock_plugin


def create_mock_computers(
    computers_spec: Mapping[DeviceName, AbstractAllocMap],
) -> Mapping[DeviceName, AbstractComputePlugin]:
    """Helper to create mock compute plugins for ResourceAllocator testing."""
    return {
        device_name: create_mock_plugin(alloc_map)
        for device_name, alloc_map in computers_spec.items()
    }


def create_global_device_info(
    plugin: AbstractComputePlugin,
    alloc_map: AbstractAllocMap,
) -> GlobalDeviceInfo:
    """Helper to create GlobalDeviceInfo for ResourcePartitioner testing."""
    devices: list[AbstractComputeDevice] = []
    for dev_id in alloc_map.device_slots.keys():
        mock_device: AbstractComputeDevice = Mock(spec=AbstractComputeDevice)
        mock_device.device_id = dev_id
        devices.append(mock_device)

    return GlobalDeviceInfo(
        plugin=plugin,
        devices=devices,
        alloc_map=alloc_map,
    )


@pytest.fixture
def mock_etcd() -> AsyncEtcd:
    """Create a minimal mock etcd for testing."""
    mock: AsyncEtcd = Mock(spec=AsyncEtcd)
    return mock


def setup_mock_resources(
    monkeypatch: pytest.MonkeyPatch,
    computers: Mapping[DeviceName, AbstractComputePlugin],
) -> None:
    """Helper to mock resource loading for ResourceAllocator tests."""

    async def _mock_load(
        self: ResourceAllocator,
    ) -> Mapping[DeviceName, AbstractComputePlugin]:
        return computers

    def _mock_calculate_total_slots(self: ResourceAllocator) -> Mapping[SlotName, Decimal]:
        total_slots: dict[SlotName, Decimal] = {}
        for ctx in self.computers.values():
            for slot_info in ctx.alloc_map.device_slots.values():
                if slot_info.slot_name not in total_slots:
                    total_slots[slot_info.slot_name] = Decimal("0")
                total_slots[slot_info.slot_name] += slot_info.amount
        return total_slots

    async def _mock_scan(self: ResourceAllocator) -> Mapping[SlotName, Decimal]:
        return _mock_calculate_total_slots(self)

    monkeypatch.setattr(
        "ai.backend.agent.resources.ResourceAllocator._load_resources",
        _mock_load,
    )
    monkeypatch.setattr(
        "ai.backend.agent.resources.ResourceAllocator._scan_available_resources",
        _mock_scan,
    )


# =============================================================================
# ResourcePartitioner Unit Tests
# =============================================================================


class TestNaturalSortKey:
    """Unit tests for _natural_sort_key helper function."""

    def test_simple_numeric_suffix(self) -> None:
        """Test sorting with simple numeric suffixes."""
        device_ids = [DeviceId("cuda0"), DeviceId("cuda1"), DeviceId("cuda10"), DeviceId("cuda2")]
        sorted_ids = sorted(device_ids, key=_natural_sort_key)
        assert sorted_ids == [
            DeviceId("cuda0"),
            DeviceId("cuda1"),
            DeviceId("cuda2"),
            DeviceId("cuda10"),
        ]

    def test_purely_numeric_ids(self) -> None:
        """Test sorting with purely numeric IDs."""
        device_ids = [DeviceId("0"), DeviceId("1"), DeviceId("10"), DeviceId("2")]
        sorted_ids = sorted(device_ids, key=_natural_sort_key)
        assert sorted_ids == [DeviceId("0"), DeviceId("1"), DeviceId("2"), DeviceId("10")]

    def test_complex_device_ids(self) -> None:
        """Test sorting with complex device IDs like nvme partitions."""
        device_ids = [DeviceId("nvme0n1p1"), DeviceId("nvme0n1p10"), DeviceId("nvme0n1p2")]
        sorted_ids = sorted(device_ids, key=_natural_sort_key)
        assert sorted_ids == [
            DeviceId("nvme0n1p1"),
            DeviceId("nvme0n1p2"),
            DeviceId("nvme0n1p10"),
        ]


class TestResourcePartitionerAssignments:
    """Unit tests for ResourcePartitioner.generate_*_assignments methods."""

    def _create_global_device_map(
        self,
        specs: Mapping[DeviceName, AbstractAllocMap],
    ) -> Mapping[DeviceName, GlobalDeviceInfo]:
        """Helper to create GlobalDeviceMap for testing."""
        result = {}
        for device_name, alloc_map in specs.items():
            plugin = create_mock_plugin(alloc_map)
            result[device_name] = create_global_device_info(plugin, alloc_map)
        return result

    def test_shared_returns_all_devices(self) -> None:
        """SHARED mode returns DevicePartition with all device IDs."""
        global_devices = self._create_global_device_map({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(4)
            }),
        })

        result = ResourcePartitioner.generate_shared_assignments(global_devices)

        # Result is defaultdict - any AgentId gets the same assignment
        any_agent = AgentId("any-agent")
        assert DeviceName("cuda") in result[any_agent]
        partition = result[any_agent][DeviceName("cuda")]
        assert isinstance(partition, DevicePartition)
        assert len(partition.device_ids) == 4

    def test_autosplit_partitions_devices_exclusively(self) -> None:
        """AUTO_SPLIT partitions devices exclusively between agents."""
        global_devices = self._create_global_device_map({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(4)
            }),
        })
        agent_ids = [AgentId("agent1"), AgentId("agent2")]
        available_slots = {SlotName("cuda.device"): Decimal("4")}

        result = ResourcePartitioner.generate_autosplit_assignments(
            global_devices, agent_ids, available_slots
        )

        # Each agent gets their own assignment
        assert AgentId("agent1") in result
        assert AgentId("agent2") in result

        # Each agent gets 2 devices (DevicePartition)
        agent1_cuda = result[AgentId("agent1")][DeviceName("cuda")]
        agent2_cuda = result[AgentId("agent2")][DeviceName("cuda")]
        assert isinstance(agent1_cuda, DevicePartition)
        assert isinstance(agent2_cuda, DevicePartition)
        assert len(agent1_cuda.device_ids) == 2
        assert len(agent2_cuda.device_ids) == 2

        # No overlap
        assert not set(agent1_cuda.device_ids) & set(agent2_cuda.device_ids)

    def test_autosplit_shared_device_uses_slot_partition(self) -> None:
        """AUTO_SPLIT uses SlotPartition for shared devices (mem)."""
        global_devices = self._create_global_device_map({
            DeviceName("mem"): create_fraction_alloc_map({
                DeviceId("root"): (SlotName("mem"), Decimal("16000000000")),
            }),
        })
        agent_ids = [AgentId("agent1"), AgentId("agent2")]
        available_slots = {SlotName("mem"): Decimal("16000000000")}

        result = ResourcePartitioner.generate_autosplit_assignments(
            global_devices, agent_ids, available_slots
        )

        # Memory should be SlotPartition (shared device)
        agent1_mem = result[AgentId("agent1")][DeviceName("mem")]
        agent2_mem = result[AgentId("agent2")][DeviceName("mem")]
        assert isinstance(agent1_mem, SlotPartition)
        assert isinstance(agent2_mem, SlotPartition)

        # Each agent gets half the memory
        assert agent1_mem.slots[SlotName("mem")] == Decimal("8000000000")
        assert agent2_mem.slots[SlotName("mem")] == Decimal("8000000000")

    def test_autosplit_uneven_distribution(self) -> None:
        """AUTO_SPLIT distributes remainder to first agents."""
        global_devices = self._create_global_device_map({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(5)
            }),
        })
        agent_ids = [AgentId("agent1"), AgentId("agent2"), AgentId("agent3")]
        available_slots = {SlotName("cuda.device"): Decimal("5")}

        result = ResourcePartitioner.generate_autosplit_assignments(
            global_devices, agent_ids, available_slots
        )

        # 5 devices / 3 agents = [2, 2, 1]
        partition1 = result[AgentId("agent1")][DeviceName("cuda")]
        partition2 = result[AgentId("agent2")][DeviceName("cuda")]
        partition3 = result[AgentId("agent3")][DeviceName("cuda")]
        assert isinstance(partition1, DevicePartition)
        assert isinstance(partition2, DevicePartition)
        assert isinstance(partition3, DevicePartition)
        assert len(partition1.device_ids) == 2
        assert len(partition2.device_ids) == 2
        assert len(partition3.device_ids) == 1

    def test_autosplit_more_agents_than_devices(self) -> None:
        """AUTO_SPLIT: some agents get zero devices when agents > devices."""
        global_devices = self._create_global_device_map({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(2)
            }),
        })
        agent_ids = [AgentId(f"agent{i}") for i in range(1, 6)]  # 5 agents
        available_slots = {SlotName("cuda.device"): Decimal("2")}

        result = ResourcePartitioner.generate_autosplit_assignments(
            global_devices, agent_ids, available_slots
        )

        # 2 devices / 5 agents = [1, 1, 0, 0, 0]
        partition1 = result[AgentId("agent1")][DeviceName("cuda")]
        partition2 = result[AgentId("agent2")][DeviceName("cuda")]
        partition3 = result[AgentId("agent3")][DeviceName("cuda")]
        partition4 = result[AgentId("agent4")][DeviceName("cuda")]
        partition5 = result[AgentId("agent5")][DeviceName("cuda")]

        assert isinstance(partition1, DevicePartition)
        assert isinstance(partition2, DevicePartition)
        assert isinstance(partition3, DevicePartition)
        assert isinstance(partition4, DevicePartition)
        assert isinstance(partition5, DevicePartition)

        assert len(partition1.device_ids) == 1
        assert len(partition2.device_ids) == 1
        assert len(partition3.device_ids) == 0
        assert len(partition4.device_ids) == 0
        assert len(partition5.device_ids) == 0

    def test_autosplit_zero_devices(self) -> None:
        """AUTO_SPLIT: handles device type with zero devices gracefully."""
        global_devices = self._create_global_device_map({
            DeviceName("cuda"): create_discrete_alloc_map({}),  # No devices
        })
        agent_ids = [AgentId("agent1"), AgentId("agent2")]
        available_slots = {SlotName("cuda.device"): Decimal("0")}

        result = ResourcePartitioner.generate_autosplit_assignments(
            global_devices, agent_ids, available_slots
        )

        # All agents get empty DevicePartition
        partition1 = result[AgentId("agent1")][DeviceName("cuda")]
        partition2 = result[AgentId("agent2")][DeviceName("cuda")]

        assert isinstance(partition1, DevicePartition)
        assert isinstance(partition2, DevicePartition)
        assert len(partition1.device_ids) == 0
        assert len(partition2.device_ids) == 0

    def test_manual_assigns_configured_devices(self) -> None:
        global_devices = self._create_global_device_map({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId(str(i)): (SlotName("cpu"), Decimal("1")) for i in range(8)
            }),
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(4)
            }),
        })

        agent1_config = Mock()
        agent1_config.agent.defaulted_id = "agent-1"
        agent1_config.resource.allocations.cpu = [
            DeviceId("0"),
            DeviceId("1"),
            DeviceId("2"),
            DeviceId("3"),
        ]
        agent1_config.resource.allocations.devices = {
            DeviceName("cuda"): [DeviceId("cuda0"), DeviceId("cuda1")]
        }

        agent2_config = Mock()
        agent2_config.agent.defaulted_id = "agent-2"
        agent2_config.resource.allocations.cpu = [
            DeviceId("4"),
            DeviceId("5"),
            DeviceId("6"),
            DeviceId("7"),
        ]
        agent2_config.resource.allocations.devices = {
            DeviceName("cuda"): [DeviceId("cuda2"), DeviceId("cuda3")]
        }

        result = ResourcePartitioner.generate_manual_assignments(
            global_devices, [agent1_config, agent2_config]
        )

        agent1_cpu = result[AgentId("agent-1")][DeviceName("cpu")]
        assert isinstance(agent1_cpu, DevicePartition)
        assert set(agent1_cpu.device_ids) == {
            DeviceId("0"),
            DeviceId("1"),
            DeviceId("2"),
            DeviceId("3"),
        }

        agent1_cuda = result[AgentId("agent-1")][DeviceName("cuda")]
        assert isinstance(agent1_cuda, DevicePartition)
        assert set(agent1_cuda.device_ids) == {DeviceId("cuda0"), DeviceId("cuda1")}

        agent2_cpu = result[AgentId("agent-2")][DeviceName("cpu")]
        assert isinstance(agent2_cpu, DevicePartition)
        assert set(agent2_cpu.device_ids) == {
            DeviceId("4"),
            DeviceId("5"),
            DeviceId("6"),
            DeviceId("7"),
        }

        agent2_cuda = result[AgentId("agent-2")][DeviceName("cuda")]
        assert isinstance(agent2_cuda, DevicePartition)
        assert set(agent2_cuda.device_ids) == {DeviceId("cuda2"), DeviceId("cuda3")}

    def test_manual_raises_error_for_unknown_device_name(self) -> None:
        global_devices = self._create_global_device_map({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId(str(i)): (SlotName("cpu"), Decimal("1")) for i in range(4)
            }),
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.device"), Decimal("1"))
            }),
        })

        agent_config = Mock()
        agent_config.agent.defaulted_id = "agent-1"
        agent_config.resource.allocations.cpu = [DeviceId("0"), DeviceId("1")]
        agent_config.resource.allocations.devices = {DeviceName("tpu"): [DeviceId("tpu0")]}

        with pytest.raises(InvalidResourceConfigError) as exc_info:
            ResourcePartitioner.generate_manual_assignments(global_devices, [agent_config])

        assert "Unknown device 'tpu'" in str(exc_info.value)

    def test_manual_raises_error_for_unknown_device_id(self) -> None:
        global_devices = self._create_global_device_map({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId(str(i)): (SlotName("cpu"), Decimal("1")) for i in range(4)
            }),
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.device"), Decimal("1"))
            }),
        })

        agent_config = Mock()
        agent_config.agent.defaulted_id = "agent-1"
        agent_config.resource.allocations.cpu = [DeviceId("0"), DeviceId("1")]
        agent_config.resource.allocations.devices = {DeviceName("cuda"): [DeviceId("cuda99")]}

        with pytest.raises(InvalidResourceConfigError) as exc_info:
            ResourcePartitioner.generate_manual_assignments(global_devices, [agent_config])

        assert "Unknown device ID 'cuda99'" in str(exc_info.value)

    def test_manual_raises_error_for_duplicate_device_across_agents(self) -> None:
        global_devices = self._create_global_device_map({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId(str(i)): (SlotName("cpu"), Decimal("1")) for i in range(8)
            }),
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(4)
            }),
        })

        agent1_config = Mock()
        agent1_config.agent.defaulted_id = "agent-1"
        agent1_config.resource.allocations.cpu = [DeviceId("0"), DeviceId("1")]
        agent1_config.resource.allocations.devices = {
            DeviceName("cuda"): [DeviceId("cuda0"), DeviceId("cuda1")]
        }

        agent2_config = Mock()
        agent2_config.agent.defaulted_id = "agent-2"
        agent2_config.resource.allocations.cpu = [DeviceId("2"), DeviceId("3")]
        agent2_config.resource.allocations.devices = {
            DeviceName("cuda"): [DeviceId("cuda1"), DeviceId("cuda2")]  # cuda1 is duplicate
        }

        with pytest.raises(InvalidResourceConfigError) as exc_info:
            ResourcePartitioner.generate_manual_assignments(
                global_devices, [agent1_config, agent2_config]
            )

        assert "assigned to multiple agents" in str(exc_info.value)
        assert "cuda1" in str(exc_info.value)


# =============================================================================
# ResourceAllocator Integration Tests
# =============================================================================


class TestResourceAllocatorSharedMode:
    """Integration tests for ResourceAllocator in SHARED mode."""

    async def test_all_agents_see_all_resources(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """SHARED mode: all agents see full resources."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.SHARED,
            num_agents=2,
        )
        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # Both agents see full resources
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("8")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("8")

        await allocator.__aexit__(None, None, None)

    async def test_no_reserved_slots(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """SHARED mode: no resources reserved between agents."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.SHARED,
            num_agents=2,
        )
        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cpu")] == Decimal("0")
        assert reserved2[SlotName("cpu")] == Decimal("0")

        await allocator.__aexit__(None, None, None)

    async def test_scaling_factor_is_one(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """SHARED mode: scaling factor is 1.0 for all slots."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.SHARED,
            num_agents=2,
        )
        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        factor1 = allocator.get_resource_scaling_factor(AgentId("agent1"))
        factor2 = allocator.get_resource_scaling_factor(AgentId("agent2"))
        assert factor1[SlotName("cpu")] == Decimal("1.0")
        assert factor2[SlotName("cpu")] == Decimal("1.0")

        await allocator.__aexit__(None, None, None)


class TestResourceAllocatorAutoSplitMode:
    """Integration tests for ResourceAllocator in AUTO_SPLIT mode."""

    async def test_devices_partitioned_exclusively(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AUTO_SPLIT: devices are partitioned exclusively between agents."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(4)
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        agent1_devices = set(agent1_computers[DeviceName("cuda")].alloc_map.device_slots.keys())
        agent2_devices = set(agent2_computers[DeviceName("cuda")].alloc_map.device_slots.keys())

        # Each agent gets 2 devices
        assert len(agent1_devices) == 2
        assert len(agent2_devices) == 2
        # No overlap
        assert not agent1_devices & agent2_devices

        await allocator.__aexit__(None, None, None)

    async def test_uneven_device_distribution(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AUTO_SPLIT: uneven devices distributed with remainder to first agents."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=3,
        )
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(5)
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # 5 devices / 3 agents = [2, 2, 1]
        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))

        assert len(agent1_computers[DeviceName("cuda")].alloc_map.device_slots) == 2
        assert len(agent2_computers[DeviceName("cuda")].alloc_map.device_slots) == 2
        assert len(agent3_computers[DeviceName("cuda")].alloc_map.device_slots) == 1

        await allocator.__aexit__(None, None, None)

    async def test_reserved_slots_reflect_partitioning(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AUTO_SPLIT: reserved slots = total - allocated."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )
        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.shares"), Decimal("1.0")) for i in range(4)
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # Each agent gets 2 devices (2.0 shares), reserved = 4.0 - 2.0 = 2.0
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cuda.shares")] == Decimal("2.0")
        assert reserved2[SlotName("cuda.shares")] == Decimal("2.0")

        await allocator.__aexit__(None, None, None)

    async def test_scaling_factor_even_distribution(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AUTO_SPLIT: scaling factor is proportional to allocation (even case).

        With even distribution, proportional scaling equals 1/n.
        2 agents, 4 devices → each gets 2 → scaling = 2/4 = 0.5
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )
        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId(str(i)): (SlotName("cpu"), Decimal("1")) for i in range(4)
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        factor1 = allocator.get_resource_scaling_factor(AgentId("agent1"))
        factor2 = allocator.get_resource_scaling_factor(AgentId("agent2"))
        assert factor1[SlotName("cpu")] == Decimal("0.5")
        assert factor2[SlotName("cpu")] == Decimal("0.5")

        await allocator.__aexit__(None, None, None)

    async def test_scaling_factor_uneven_distribution(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AUTO_SPLIT: scaling factor is proportional to actual allocation (uneven case).

        With uneven distribution, proportional scaling differs from naive 1/n.
        3 agents, 5 devices → distribution is [2, 2, 1]:
        - agent1: 2/5 = 0.4
        - agent2: 2/5 = 0.4
        - agent3: 1/5 = 0.2

        A naive 1/n approach would give 1/3 ≈ 0.333 for all agents, which is
        incorrect because agent3 only has 1 device while others have 2.
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=3,
        )
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(5)
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        factor1 = allocator.get_resource_scaling_factor(AgentId("agent1"))
        factor2 = allocator.get_resource_scaling_factor(AgentId("agent2"))
        factor3 = allocator.get_resource_scaling_factor(AgentId("agent3"))

        # Proportional scaling: allocated / total
        assert factor1[SlotName("cuda.device")] == Decimal("2") / Decimal("5")
        assert factor2[SlotName("cuda.device")] == Decimal("2") / Decimal("5")
        assert factor3[SlotName("cuda.device")] == Decimal("1") / Decimal("5")

        # Verify this is NOT the naive 1/n approach
        naive_factor = Decimal("1") / Decimal("3")
        assert factor1[SlotName("cuda.device")] != naive_factor
        assert factor3[SlotName("cuda.device")] != naive_factor

        await allocator.__aexit__(None, None, None)

    async def test_single_agent_gets_all_devices(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AUTO_SPLIT with 1 agent: behaves like SHARED."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=1,
        )
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(4)
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        assert len(agent1_computers[DeviceName("cuda")].alloc_map.device_slots) == 4

        await allocator.__aexit__(None, None, None)

    async def test_mixed_device_types(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AUTO_SPLIT: CPU devices partitioned, memory slots divided."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )
        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId(f"cpu{i}"): (SlotName("cpu"), Decimal("1")) for i in range(4)
            }),
            DeviceName("mem"): create_fraction_alloc_map({
                DeviceId("root"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("16G"))),
            }),
        })
        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # CPU: 4 devices / 2 agents = 2 each (exclusive)
        assert len(agent1_computers[DeviceName("cpu")].alloc_map.device_slots) == 2
        assert len(agent2_computers[DeviceName("cpu")].alloc_map.device_slots) == 2

        # Memory: shared device, both see same device with divided slots
        assert len(agent1_computers[DeviceName("mem")].alloc_map.device_slots) == 1
        assert len(agent2_computers[DeviceName("mem")].alloc_map.device_slots) == 1

        await allocator.__aexit__(None, None, None)
