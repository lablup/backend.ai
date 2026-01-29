"""
Unit tests for ResourceAllocator and multi-agent resource allocation.

Tests the ResourceAllocator implementation that handles SHARED, AUTO_SPLIT, and MANUAL
resource allocation modes for multiple agents running on the same physical host.
"""

from __future__ import annotations

from collections.abc import Mapping
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
from ai.backend.agent.resources import (
    AbstractComputeDevice,
    AbstractComputePlugin,
    ResourceAllocator,
    _natural_sort_key,
    distribute_devices,
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
            agent_override: dict = {
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


def _get_slot_types_for_device(
    device_name: DeviceName, alloc_map: AbstractAllocMap
) -> list[tuple[SlotName, SlotTypes]]:
    """Determine appropriate slot_types based on device name and alloc_map."""
    # Get the slot name from the first device slot
    first_slot = next(iter(alloc_map.device_slots.values()))
    slot_name = first_slot.slot_name

    # CPU uses COUNT, memory uses BYTES, others use BYTES (for shares)
    if device_name == DeviceName("cpu"):
        return [(slot_name, SlotTypes.COUNT)]
    if device_name == DeviceName("mem"):
        return [(slot_name, SlotTypes.BYTES)]
    # Accelerators
    return [(slot_name, SlotTypes.BYTES)]


def create_mock_computers(
    computers_spec: Mapping[DeviceName, AbstractAllocMap],
) -> tuple[Mapping[DeviceName, AbstractComputePlugin], Mapping[DeviceName, AbstractAllocMap]]:
    """
    Helper to create mock compute plugins for testing.

    This function is isolated to contain the mock creation and type ignores.
    Returns both the mock plugins and the original spec for use in setup_mock_resources.
    """
    result: dict[DeviceName, AbstractComputePlugin] = {}
    for device_name, alloc_map in computers_spec.items():
        mock_plugin: AbstractComputePlugin = Mock(spec=AbstractComputePlugin)  # type: ignore[assignment]
        mock_plugin.get_metadata.return_value = {"slot_name": str(device_name)}  # type: ignore[attr-defined]

        # Set the plugin key and slot_types (used by _get_partitioner and _cpu_device_name/_mem_device_name)
        mock_plugin.key = device_name  # type: ignore[attr-defined]
        mock_plugin.slot_types = _get_slot_types_for_device(device_name, alloc_map)  # type: ignore[attr-defined]

        # Create mock devices for each device_id in the alloc_map
        mock_devices: list[AbstractComputeDevice] = []
        for dev_id, slot_info in alloc_map.device_slots.items():
            mock_device: AbstractComputeDevice = Mock(spec=AbstractComputeDevice)  # type: ignore[assignment]
            mock_device.device_id = dev_id  # type: ignore[attr-defined]
            # For memory devices, set memory_size from the slot amount
            if device_name == DeviceName("mem"):
                mock_device.memory_size = int(slot_info.amount)  # type: ignore[attr-defined]
            else:
                mock_device.memory_size = 0  # type: ignore[attr-defined]
            mock_devices.append(mock_device)

        # Create a fresh alloc_map for each call
        async def _create_alloc_map(original_map: AbstractAllocMap = alloc_map) -> AbstractAllocMap:  # type: ignore[misc]
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

        # Create available_slots return value from alloc_map
        available_slots_dict: dict[SlotName, Decimal] = {}
        for slot_info in alloc_map.device_slots.values():
            if slot_info.slot_name not in available_slots_dict:
                available_slots_dict[slot_info.slot_name] = Decimal("0")
            available_slots_dict[slot_info.slot_name] += slot_info.amount

        mock_plugin.create_alloc_map = _create_alloc_map  # type: ignore[attr-defined,assignment]
        mock_plugin.list_devices = AsyncMock(return_value=mock_devices)  # type: ignore[attr-defined,method-assign]
        mock_plugin.available_slots = AsyncMock(return_value=available_slots_dict)  # type: ignore[attr-defined,method-assign]
        mock_plugin.cleanup = AsyncMock(return_value=None)  # type: ignore[attr-defined,method-assign]

        result[device_name] = mock_plugin
    return result, computers_spec


@pytest.fixture
def mock_etcd() -> AsyncEtcd:
    """Create a minimal mock etcd for testing."""
    mock: AsyncEtcd = Mock(spec=AsyncEtcd)  # type: ignore[assignment]
    return mock


def setup_mock_resources(
    monkeypatch: pytest.MonkeyPatch,
    computers: Mapping[DeviceName, AbstractComputePlugin],
    computers_spec: Mapping[DeviceName, AbstractAllocMap],
) -> None:
    """Helper to mock resource loading for a specific test."""

    async def _mock_load(self: ResourceAllocator) -> Mapping[DeviceName, AbstractComputePlugin]:
        return computers

    # Pre-calculate total slots from the spec (used by _calculate_total_slots)
    async def _mock_calculate_total_slots_from_spec(
        self: ResourceAllocator,
    ) -> Mapping[SlotName, Decimal]:
        total_slots: dict[SlotName, Decimal] = {}
        for alloc_map in computers_spec.values():
            for slot_info in alloc_map.device_slots.values():
                if slot_info.slot_name not in total_slots:
                    total_slots[slot_info.slot_name] = Decimal("0")
                total_slots[slot_info.slot_name] += slot_info.amount
        return total_slots

    async def _mock_scan(self: ResourceAllocator) -> Mapping[SlotName, Decimal]:
        # Returns same as _calculate_total_slots
        return await _mock_calculate_total_slots_from_spec(self)

    monkeypatch.setattr(
        "ai.backend.agent.resources.ResourceAllocator._load_resources",
        _mock_load,
    )
    monkeypatch.setattr(
        "ai.backend.agent.resources.ResourceAllocator._scan_available_resources",
        _mock_scan,
    )
    monkeypatch.setattr(
        "ai.backend.agent.resources.ResourceAllocator._calculate_total_slots",
        _mock_calculate_total_slots_from_spec,
    )


class TestNaturalSort:
    """Tests for natural sorting of device IDs."""

    def test_natural_sort_key_pure_numeric(self) -> None:
        """Pure numeric IDs should sort numerically."""
        ids = [DeviceId("0"), DeviceId("1"), DeviceId("10"), DeviceId("2"), DeviceId("9")]
        sorted_ids = sorted(ids, key=_natural_sort_key)
        assert sorted_ids == [
            DeviceId("0"),
            DeviceId("1"),
            DeviceId("2"),
            DeviceId("9"),
            DeviceId("10"),
        ]

    def test_natural_sort_key_prefixed(self) -> None:
        """Prefixed IDs like cuda0, cuda10 should sort by prefix then number."""
        ids = [DeviceId("cuda0"), DeviceId("cuda10"), DeviceId("cuda2"), DeviceId("cuda1")]
        sorted_ids = sorted(ids, key=_natural_sort_key)
        assert sorted_ids == [
            DeviceId("cuda0"),
            DeviceId("cuda1"),
            DeviceId("cuda2"),
            DeviceId("cuda10"),
        ]

    def test_natural_sort_key_mixed_prefixes(self) -> None:
        """Different prefixes should sort alphabetically, then by number."""
        ids = [DeviceId("gpu1"), DeviceId("cuda0"), DeviceId("gpu0"), DeviceId("cuda1")]
        sorted_ids = sorted(ids, key=_natural_sort_key)
        assert sorted_ids == [
            DeviceId("cuda0"),
            DeviceId("cuda1"),
            DeviceId("gpu0"),
            DeviceId("gpu1"),
        ]

    def test_natural_sort_key_numbers_in_middle(self) -> None:
        """Numbers anywhere in string should be handled (e.g., nvme0n1p1)."""
        ids = [
            DeviceId("nvme0n1p10"),
            DeviceId("nvme0n1p2"),
            DeviceId("nvme0n1p1"),
            DeviceId("nvme1n1p1"),
        ]
        sorted_ids = sorted(ids, key=_natural_sort_key)
        assert sorted_ids == [
            DeviceId("nvme0n1p1"),
            DeviceId("nvme0n1p2"),
            DeviceId("nvme0n1p10"),
            DeviceId("nvme1n1p1"),
        ]

    def test_distribute_devices_numeric_ids(self) -> None:
        """CPU-style numeric IDs should distribute in natural order."""
        device_ids = [DeviceId(str(i)) for i in [0, 1, 10, 11, 12, 2, 3, 4, 5, 6, 7, 8, 9]]
        agent_ids = [AgentId("agent-1"), AgentId("agent-2"), AgentId("agent-3")]

        result = distribute_devices(device_ids, agent_ids)

        # 13 devices / 3 agents = 4 base + 1 extra for first agent
        # Should be: [0,1,2,3,4], [5,6,7,8], [9,10,11,12]
        assert result[AgentId("agent-1")] == [DeviceId(str(i)) for i in [0, 1, 2, 3, 4]]
        assert result[AgentId("agent-2")] == [DeviceId(str(i)) for i in [5, 6, 7, 8]]
        assert result[AgentId("agent-3")] == [DeviceId(str(i)) for i in [9, 10, 11, 12]]

    def test_distribute_devices_cuda_ids(self) -> None:
        """CUDA-style prefixed IDs should distribute in natural order."""
        device_ids = [DeviceId(f"cuda{i}") for i in [0, 1, 10, 2, 3, 4]]
        agent_ids = [AgentId("agent-1"), AgentId("agent-2")]

        result = distribute_devices(device_ids, agent_ids)

        # 6 devices / 2 agents = 3 each
        # Natural order: cuda0, cuda1, cuda2, cuda3, cuda4, cuda10
        assert result[AgentId("agent-1")] == [
            DeviceId("cuda0"),
            DeviceId("cuda1"),
            DeviceId("cuda2"),
        ]
        assert result[AgentId("agent-2")] == [
            DeviceId("cuda3"),
            DeviceId("cuda4"),
            DeviceId("cuda10"),
        ]


class TestSharedMode:
    async def test_no_restrictions(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.SHARED,
            num_agents=2,
        )

        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # In SHARED mode, both agents get full resources
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("8")
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("1.0")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("8")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("1.0")

        # No resources reserved in SHARED mode
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cpu")] == Decimal("0")
        assert reserved1[SlotName("cuda.shares")] == Decimal("0")
        assert reserved2[SlotName("cpu")] == Decimal("0")
        assert reserved2[SlotName("cuda.shares")] == Decimal("0")

        await allocator.__aexit__(None, None, None)

    async def test_with_reserved_resources(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.SHARED,
            reserved_cpu=2,
            reserved_mem="4G",
        )

        # Create 8 CPU devices (1 core each). Single mem device with 16G.
        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId(f"cpu{i}"): (SlotName("cpu"), Decimal("1")) for i in range(8)
            }),
            DeviceName("mem"): create_fraction_alloc_map({
                DeviceId("root"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("16G"))),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))

        # alloc_map shows original hardware amounts (unchanged)
        for i in range(8):
            assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
                DeviceId(f"cpu{i}")
            ].amount == Decimal("1")
        assert agent1_computers[DeviceName("mem")].alloc_map.device_slots[
            DeviceId("root")
        ].amount == Decimal(BinarySize.finite_from_str("16G"))

        # SHARED mode: reserved_slots = system reserved only (not from other agents)
        # For CPU: total=8, available=6, reserved_slots = 8 - 6 = 2
        # For mem: total=16G, available=12G, reserved_slots = 16G - 12G = 4G
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        assert reserved1[SlotName("cpu")] == Decimal("2")
        assert reserved1[SlotName("mem")] == Decimal(BinarySize.finite_from_str("4G"))

        await allocator.__aexit__(None, None, None)


class TestAutoSplitMode:
    async def test_multi_gpu_whole_device_assignment(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test AUTO_SPLIT with 4 GPUs, 2 agents - each agent gets 2 whole devices."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )

        # 4 GPU devices with 1.0 shares each
        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.shares"), Decimal("1.0")) for i in range(4)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # With whole-device assignment (divmod):
        # 4 devices / 2 agents = 2 devices each
        # Agent1 gets: cuda0, cuda1
        # Agent2 gets: cuda2, cuda3
        agent1_slots = agent1_computers[DeviceName("cuda")].alloc_map.device_slots
        agent2_slots = agent2_computers[DeviceName("cuda")].alloc_map.device_slots

        assert len(agent1_slots) == 2
        assert DeviceId("cuda0") in agent1_slots
        assert DeviceId("cuda1") in agent1_slots
        assert agent1_slots[DeviceId("cuda0")].amount == Decimal("1.0")
        assert agent1_slots[DeviceId("cuda1")].amount == Decimal("1.0")

        assert len(agent2_slots) == 2
        assert DeviceId("cuda2") in agent2_slots
        assert DeviceId("cuda3") in agent2_slots
        assert agent2_slots[DeviceId("cuda2")].amount == Decimal("1.0")
        assert agent2_slots[DeviceId("cuda3")].amount == Decimal("1.0")

        # Verify device mutual exclusivity - no device appears in both partitions
        agent1_device_ids = set(agent1_slots.keys())
        agent2_device_ids = set(agent2_slots.keys())
        assert agent1_device_ids.isdisjoint(agent2_device_ids)

        await allocator.__aexit__(None, None, None)

    async def test_uneven_device_distribution(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test AUTO_SPLIT with 5 GPUs, 3 agents - divmod distribution."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=3,
        )

        # 5 GPU devices
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(5)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))

        # divmod(5, 3) = (1, 2)
        # First 2 agents get 2 devices each, last agent gets 1 device
        # Agent1: cuda0, cuda1
        # Agent2: cuda2, cuda3
        # Agent3: cuda4
        agent1_slots = agent1_computers[DeviceName("cuda")].alloc_map.device_slots
        agent2_slots = agent2_computers[DeviceName("cuda")].alloc_map.device_slots
        agent3_slots = agent3_computers[DeviceName("cuda")].alloc_map.device_slots

        assert len(agent1_slots) == 2
        assert len(agent2_slots) == 2
        assert len(agent3_slots) == 1

        assert DeviceId("cuda0") in agent1_slots
        assert DeviceId("cuda1") in agent1_slots
        assert DeviceId("cuda2") in agent2_slots
        assert DeviceId("cuda3") in agent2_slots
        assert DeviceId("cuda4") in agent3_slots

        # Verify device mutual exclusivity
        all_device_ids = (
            set(agent1_slots.keys()) | set(agent2_slots.keys()) | set(agent3_slots.keys())
        )
        assert len(all_device_ids) == 5  # All 5 devices accounted for

        await allocator.__aexit__(None, None, None)

    async def test_more_agents_than_devices(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test AUTO_SPLIT when M > N (more agents than devices)."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=4,
        )

        # 2 GPU devices, 4 agents
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(2)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))
        agent4_computers = allocator.get_computers(AgentId("agent4"))

        # divmod(2, 4) = (0, 2)
        # First 2 agents get 1 device each, remaining agents get 0 devices
        # Agent1: cuda0
        # Agent2: cuda1
        # Agent3: (empty)
        # Agent4: (empty)
        agent1_slots = agent1_computers[DeviceName("cuda")].alloc_map.device_slots
        agent2_slots = agent2_computers[DeviceName("cuda")].alloc_map.device_slots
        agent3_slots = agent3_computers[DeviceName("cuda")].alloc_map.device_slots
        agent4_slots = agent4_computers[DeviceName("cuda")].alloc_map.device_slots

        assert len(agent1_slots) == 1
        assert len(agent2_slots) == 1
        assert len(agent3_slots) == 0
        assert len(agent4_slots) == 0

        assert DeviceId("cuda0") in agent1_slots
        assert DeviceId("cuda1") in agent2_slots

        await allocator.__aexit__(None, None, None)

    async def test_single_device_multiple_agents(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test AUTO_SPLIT with 1 device, 3 agents - only first agent gets device."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=3,
        )

        # 1 GPU device
        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))

        # divmod(1, 3) = (0, 1)
        # First 1 agent gets 1 device, remaining get 0
        agent1_slots = agent1_computers[DeviceName("cuda")].alloc_map.device_slots
        agent2_slots = agent2_computers[DeviceName("cuda")].alloc_map.device_slots
        agent3_slots = agent3_computers[DeviceName("cuda")].alloc_map.device_slots

        assert len(agent1_slots) == 1
        assert len(agent2_slots) == 0
        assert len(agent3_slots) == 0

        assert DeviceId("cuda0") in agent1_slots
        assert agent1_slots[DeviceId("cuda0")].amount == Decimal("1.0")

        await allocator.__aexit__(None, None, None)


class TestManualMode:
    async def test_cpu_mem(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test MANUAL mode with a single agent and explicit CPU/mem allocations."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.MANUAL,
            allocated_cpu=4,
            allocated_mem="8G",
            num_agents=1,  # Single agent for MANUAL mode
        )

        # Create multiple CPU devices so we can assign 4 of them
        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId(f"cpu{i}"): (SlotName("cpu"), Decimal("1")) for i in range(8)
            }),
            DeviceName("mem"): create_fraction_alloc_map({
                DeviceId("root"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("32G"))),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))

        # Agent1 gets 4 CPU devices (cpu0-cpu3) based on allocated_cpu=4
        agent1_cpu_slots = agent1_computers[DeviceName("cpu")].alloc_map.device_slots
        assert len(agent1_cpu_slots) == 4
        for i in range(4):
            assert DeviceId(f"cpu{i}") in agent1_cpu_slots

        # Agent1 gets the memory device
        agent1_mem_slots = agent1_computers[DeviceName("mem")].alloc_map.device_slots
        assert len(agent1_mem_slots) == 1
        assert DeviceId("root") in agent1_mem_slots

        await allocator.__aexit__(None, None, None)


class TestMultiDeviceScenarios:
    """Tests for realistic multi-device scenarios with whole-device assignment.

    These tests ensure the resource partitioning logic works correctly with:
    - Multiple physical devices (multi-GPU systems)
    - BEP-1016 compliant device mutual exclusivity
    """

    async def test_four_gpus_two_agents(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test 4 GPUs with 2 agents - each agent gets 2 whole GPUs."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )

        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.shares"), Decimal("1.0")) for i in range(4)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_ctx = allocator.get_computers(AgentId("agent1"))[DeviceName("cuda")]
        agent2_ctx = allocator.get_computers(AgentId("agent2"))[DeviceName("cuda")]

        # Agent1 gets cuda0, cuda1
        assert {d.device_id for d in agent1_ctx.devices} == {DeviceId("cuda0"), DeviceId("cuda1")}
        assert len(agent1_ctx.alloc_map.device_slots) == 2

        # Agent2 gets cuda2, cuda3
        assert {d.device_id for d in agent2_ctx.devices} == {DeviceId("cuda2"), DeviceId("cuda3")}
        assert len(agent2_ctx.alloc_map.device_slots) == 2

        await allocator.__aexit__(None, None, None)

    async def test_multi_device_shared_mode(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test SHARED mode with multiple GPU devices - all agents share all resources."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.SHARED,
            num_agents=3,
        )

        # 4 separate GPU devices (realistic: multi-GPU system)
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.device"), Decimal("1")) for i in range(4)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))

        # In SHARED mode, all agents see all devices
        for i in range(4):
            assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("1")
            assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("1")
            assert agent3_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("1")

        await allocator.__aexit__(None, None, None)

    async def test_calculate_total_slots_sums_all_devices(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify that total_slots correctly sums across multiple GPU devices."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.SHARED,
        )

        # Create 4 GPU devices with VRAM (realistic multi-GPU setup)
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.mem"), Decimal("8000000000"))
                for i in range(4)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # 4 GPUs × 8GB each = 32GB total VRAM
        # available_total_slots reflects total minus reserved (no reserved in this test)
        assert allocator.available_total_slots[SlotName("cuda.mem")] == Decimal("32000000000")

        await allocator.__aexit__(None, None, None)

    async def test_heterogeneous_gpu_capacities_whole_device(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test whole-device assignment with heterogeneous GPU capacities.

        4 GPUs with shares [3, 2, 2, 3], 2 agents
        With whole-device assignment:
        - Agent1: cuda0 (3) + cuda1 (2) = 5 shares total
        - Agent2: cuda2 (2) + cuda3 (3) = 5 shares total
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )

        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("3")),
                DeviceId("cuda1"): (SlotName("cuda.shares"), Decimal("2")),
                DeviceId("cuda2"): (SlotName("cuda.shares"), Decimal("2")),
                DeviceId("cuda3"): (SlotName("cuda.shares"), Decimal("3")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_ctx = allocator.get_computers(AgentId("agent1"))[DeviceName("cuda")]
        agent2_ctx = allocator.get_computers(AgentId("agent2"))[DeviceName("cuda")]

        # Agent1 gets cuda0, cuda1 (whole devices)
        assert {d.device_id for d in agent1_ctx.devices} == {DeviceId("cuda0"), DeviceId("cuda1")}
        agent1_slots = agent1_ctx.alloc_map.device_slots
        assert agent1_slots[DeviceId("cuda0")].amount == Decimal("3")
        assert agent1_slots[DeviceId("cuda1")].amount == Decimal("2")

        # Agent2 gets cuda2, cuda3 (whole devices)
        assert {d.device_id for d in agent2_ctx.devices} == {DeviceId("cuda2"), DeviceId("cuda3")}
        agent2_slots = agent2_ctx.alloc_map.device_slots
        assert agent2_slots[DeviceId("cuda2")].amount == Decimal("2")
        assert agent2_slots[DeviceId("cuda3")].amount == Decimal("3")

        # Verify device mutual exclusivity
        agent1_device_ids = set(agent1_slots.keys())
        agent2_device_ids = set(agent2_slots.keys())
        assert agent1_device_ids.isdisjoint(agent2_device_ids)

        await allocator.__aexit__(None, None, None)

    async def test_multi_cpu_devices_whole_assignment(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test whole-device assignment with multiple CPU devices.

        4 CPU devices with [2, 2, 2, 2] cores, 2 agents
        - Agent1: cpu0 (2) + cpu1 (2) = 4 cores
        - Agent2: cpu2 (2) + cpu3 (2) = 4 cores
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )

        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId("cpu0"): (SlotName("cpu"), Decimal("2")),
                DeviceId("cpu1"): (SlotName("cpu"), Decimal("2")),
                DeviceId("cpu2"): (SlotName("cpu"), Decimal("2")),
                DeviceId("cpu3"): (SlotName("cpu"), Decimal("2")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_ctx = allocator.get_computers(AgentId("agent1"))[DeviceName("cpu")]
        agent2_ctx = allocator.get_computers(AgentId("agent2"))[DeviceName("cpu")]

        # Agent1 gets cpu0, cpu1
        assert {d.device_id for d in agent1_ctx.devices} == {DeviceId("cpu0"), DeviceId("cpu1")}
        agent1_slots = agent1_ctx.alloc_map.device_slots
        assert len(agent1_slots) == 2
        assert agent1_slots[DeviceId("cpu0")].amount == Decimal("2")
        assert agent1_slots[DeviceId("cpu1")].amount == Decimal("2")

        # Agent2 gets cpu2, cpu3
        assert {d.device_id for d in agent2_ctx.devices} == {DeviceId("cpu2"), DeviceId("cpu3")}
        agent2_slots = agent2_ctx.alloc_map.device_slots
        assert len(agent2_slots) == 2
        assert agent2_slots[DeviceId("cpu2")].amount == Decimal("2")
        assert agent2_slots[DeviceId("cpu3")].amount == Decimal("2")

        # Verify device mutual exclusivity
        assert set(agent1_slots.keys()).isdisjoint(set(agent2_slots.keys()))

        await allocator.__aexit__(None, None, None)

    async def test_three_devices_three_agents(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test 3 devices with 3 agents - each agent gets exactly 1 device.

        divmod(3, 3) = (1, 0) means each agent gets 1 device.
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=3,
        )

        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda1"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda2"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        for i in range(1, 4):
            ctx = allocator.get_computers(AgentId(f"agent{i}"))[DeviceName("cuda")]
            assert len(ctx.alloc_map.device_slots) == 1
            expected_device = DeviceId(f"cuda{i - 1}")
            assert expected_device in ctx.alloc_map.device_slots
            assert ctx.alloc_map.device_slots[expected_device].amount == Decimal("1.0")

        await allocator.__aexit__(None, None, None)


def create_manual_multi_agent_config(
    agent_allocations: list[dict[str, Any]],
    *,
    reserved_cpu: int = 0,
    reserved_mem: str = "0",
    reserved_disk: str = "0",
) -> AgentUnifiedConfig:
    """
    Helper to create AgentUnifiedConfig for MANUAL mode with per-agent device allocations.

    Args:
        agent_allocations: List of dicts with keys:
            - id: Agent ID
            - cpu: Number of CPU cores
            - mem: Memory as string (e.g., "8G")
            - devices: Optional dict of {DeviceName: [DeviceId, ...]}
    """
    base_config: dict[str, Any] = {
        "agent": {
            "id": agent_allocations[0]["id"],
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
            "allocation_mode": ResourceAllocationMode.MANUAL,
        },
        "etcd": {
            "addr": "127.0.0.1:2379",
            "namespace": "test",
        },
    }

    agents_list = []
    for alloc in agent_allocations:
        agent_override: dict[str, Any] = {
            "agent": {"id": alloc["id"]},
            "resource": {
                "cpu": alloc["cpu"],
                "mem": BinarySize.finite_from_str(alloc["mem"]),
            },
        }
        if "devices" in alloc:
            agent_override["resource"]["devices"] = {
                DeviceName(k): [DeviceId(d) for d in v] for k, v in alloc["devices"].items()
            }
        agents_list.append(agent_override)

    base_config["agents"] = agents_list
    return AgentUnifiedConfig.model_validate(base_config)


class TestFractionalGPUScenarios:
    """Tests for fractional GPU (fGPU) scenarios with multiple agents.

    These tests verify device splitting works correctly with fGPU setups
    where each GPU can have fractional shares allocated.
    """

    async def test_auto_split_5_fgpu_3_agents(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test AUTO_SPLIT with 5 fGPU CUDA cards and 3 agents.

        Setup: 5 GPUs with 1.0 shares each, 3 agents
        Expected distribution (divmod(5, 3) = (1, 2)):
        - Agent1: cuda0, cuda1 (first agent in remainder gets extra)
        - Agent2: cuda2, cuda3 (second agent in remainder gets extra)
        - Agent3: cuda4 (remaining agent gets base quota)
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=3,
        )

        # 5 fGPU devices with fractional shares
        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda1"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda2"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda3"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda4"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_ctx = allocator.get_computers(AgentId("agent1"))[DeviceName("cuda")]
        agent2_ctx = allocator.get_computers(AgentId("agent2"))[DeviceName("cuda")]
        agent3_ctx = allocator.get_computers(AgentId("agent3"))[DeviceName("cuda")]

        # Agent1 gets cuda0, cuda1
        assert {d.device_id for d in agent1_ctx.devices} == {
            DeviceId("cuda0"),
            DeviceId("cuda1"),
        }
        assert len(agent1_ctx.alloc_map.device_slots) == 2
        assert agent1_ctx.alloc_map.device_slots[DeviceId("cuda0")].amount == Decimal("1.0")
        assert agent1_ctx.alloc_map.device_slots[DeviceId("cuda1")].amount == Decimal("1.0")

        # Agent2 gets cuda2, cuda3
        assert {d.device_id for d in agent2_ctx.devices} == {
            DeviceId("cuda2"),
            DeviceId("cuda3"),
        }
        assert len(agent2_ctx.alloc_map.device_slots) == 2
        assert agent2_ctx.alloc_map.device_slots[DeviceId("cuda2")].amount == Decimal("1.0")
        assert agent2_ctx.alloc_map.device_slots[DeviceId("cuda3")].amount == Decimal("1.0")

        # Agent3 gets cuda4
        assert {d.device_id for d in agent3_ctx.devices} == {DeviceId("cuda4")}
        assert len(agent3_ctx.alloc_map.device_slots) == 1
        assert agent3_ctx.alloc_map.device_slots[DeviceId("cuda4")].amount == Decimal("1.0")

        # Verify device mutual exclusivity
        all_devices = (
            set(agent1_ctx.alloc_map.device_slots.keys())
            | set(agent2_ctx.alloc_map.device_slots.keys())
            | set(agent3_ctx.alloc_map.device_slots.keys())
        )
        assert len(all_devices) == 5  # All 5 devices assigned

        await allocator.__aexit__(None, None, None)

    async def test_auto_split_5_fgpu_heterogeneous_shares_3_agents(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test AUTO_SPLIT with 5 fGPU cards having different share amounts.

        Setup: 5 GPUs with varying shares [2.0, 1.5, 1.0, 0.5, 1.0], 3 agents
        With whole-device assignment, agents get whole GPUs regardless of share size.
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=3,
        )

        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("2.0")),
                DeviceId("cuda1"): (SlotName("cuda.shares"), Decimal("1.5")),
                DeviceId("cuda2"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda3"): (SlotName("cuda.shares"), Decimal("0.5")),
                DeviceId("cuda4"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_ctx = allocator.get_computers(AgentId("agent1"))[DeviceName("cuda")]
        agent2_ctx = allocator.get_computers(AgentId("agent2"))[DeviceName("cuda")]
        agent3_ctx = allocator.get_computers(AgentId("agent3"))[DeviceName("cuda")]

        # Agent1 gets cuda0 (2.0) + cuda1 (1.5) = 3.5 total shares
        agent1_slots = agent1_ctx.alloc_map.device_slots
        assert DeviceId("cuda0") in agent1_slots
        assert DeviceId("cuda1") in agent1_slots
        assert agent1_slots[DeviceId("cuda0")].amount == Decimal("2.0")
        assert agent1_slots[DeviceId("cuda1")].amount == Decimal("1.5")

        # Agent2 gets cuda2 (1.0) + cuda3 (0.5) = 1.5 total shares
        agent2_slots = agent2_ctx.alloc_map.device_slots
        assert DeviceId("cuda2") in agent2_slots
        assert DeviceId("cuda3") in agent2_slots
        assert agent2_slots[DeviceId("cuda2")].amount == Decimal("1.0")
        assert agent2_slots[DeviceId("cuda3")].amount == Decimal("0.5")

        # Agent3 gets cuda4 (1.0) = 1.0 total shares
        agent3_slots = agent3_ctx.alloc_map.device_slots
        assert DeviceId("cuda4") in agent3_slots
        assert agent3_slots[DeviceId("cuda4")].amount == Decimal("1.0")

        await allocator.__aexit__(None, None, None)


class TestManualModeNonContiguous:
    """Tests for MANUAL mode with non-contiguous device assignments.

    These tests verify that explicit device assignments work correctly
    when devices are not assigned in fill-from-front order.
    """

    async def test_manual_non_contiguous_5_gpus_3_agents(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test MANUAL mode with non-contiguous GPU assignments.

        Setup: 5 GPUs, 3 agents with explicit non-contiguous assignments:
        - Agent1: cuda0, cuda3 (skipping cuda1, cuda2)
        - Agent2: cuda1, cuda4 (non-adjacent)
        - Agent3: cuda2 (single device)

        This tests that manual assignments don't require fill-from-front order.
        """
        config = create_manual_multi_agent_config([
            {
                "id": "agent1",
                "cpu": 2,
                "mem": "4G",
                "devices": {"cuda": ["cuda0", "cuda3"]},
            },
            {
                "id": "agent2",
                "cpu": 2,
                "mem": "4G",
                "devices": {"cuda": ["cuda1", "cuda4"]},
            },
            {
                "id": "agent3",
                "cpu": 2,
                "mem": "4G",
                "devices": {"cuda": ["cuda2"]},
            },
        ])

        # 5 fGPU devices
        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId(f"cpu{i}"): (SlotName("cpu"), Decimal("1")) for i in range(8)
            }),
            DeviceName("mem"): create_fraction_alloc_map({
                DeviceId("root"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("32G"))),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda1"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda2"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda3"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda4"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # Agent1 gets cuda0, cuda3 (non-contiguous)
        agent1_ctx = allocator.get_computers(AgentId("agent1"))[DeviceName("cuda")]
        assert {d.device_id for d in agent1_ctx.devices} == {
            DeviceId("cuda0"),
            DeviceId("cuda3"),
        }
        assert len(agent1_ctx.alloc_map.device_slots) == 2

        # Agent2 gets cuda1, cuda4 (non-contiguous)
        agent2_ctx = allocator.get_computers(AgentId("agent2"))[DeviceName("cuda")]
        assert {d.device_id for d in agent2_ctx.devices} == {
            DeviceId("cuda1"),
            DeviceId("cuda4"),
        }
        assert len(agent2_ctx.alloc_map.device_slots) == 2

        # Agent3 gets cuda2
        agent3_ctx = allocator.get_computers(AgentId("agent3"))[DeviceName("cuda")]
        assert {d.device_id for d in agent3_ctx.devices} == {DeviceId("cuda2")}
        assert len(agent3_ctx.alloc_map.device_slots) == 1

        # Verify all devices are assigned exactly once
        all_assigned = (
            set(agent1_ctx.alloc_map.device_slots.keys())
            | set(agent2_ctx.alloc_map.device_slots.keys())
            | set(agent3_ctx.alloc_map.device_slots.keys())
        )
        assert all_assigned == {
            DeviceId("cuda0"),
            DeviceId("cuda1"),
            DeviceId("cuda2"),
            DeviceId("cuda3"),
            DeviceId("cuda4"),
        }

        await allocator.__aexit__(None, None, None)

    async def test_manual_uneven_distribution(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test MANUAL mode with uneven device distribution.

        Setup: 5 GPUs, 3 agents with uneven assignments:
        - Agent1: cuda0, cuda1, cuda2 (3 devices)
        - Agent2: cuda3 (1 device)
        - Agent3: cuda4 (1 device)

        This tests that manual mode allows arbitrary distribution unlike AUTO_SPLIT.
        """
        config = create_manual_multi_agent_config([
            {
                "id": "agent1",
                "cpu": 4,
                "mem": "8G",
                "devices": {"cuda": ["cuda0", "cuda1", "cuda2"]},
            },
            {
                "id": "agent2",
                "cpu": 2,
                "mem": "4G",
                "devices": {"cuda": ["cuda3"]},
            },
            {
                "id": "agent3",
                "cpu": 2,
                "mem": "4G",
                "devices": {"cuda": ["cuda4"]},
            },
        ])

        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId(f"cpu{i}"): (SlotName("cpu"), Decimal("1")) for i in range(8)
            }),
            DeviceName("mem"): create_fraction_alloc_map({
                DeviceId("root"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("32G"))),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.shares"), Decimal("1.0")) for i in range(5)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # Agent1 gets 3 devices
        agent1_ctx = allocator.get_computers(AgentId("agent1"))[DeviceName("cuda")]
        assert len(agent1_ctx.alloc_map.device_slots) == 3
        assert {d.device_id for d in agent1_ctx.devices} == {
            DeviceId("cuda0"),
            DeviceId("cuda1"),
            DeviceId("cuda2"),
        }

        # Agent2 gets 1 device
        agent2_ctx = allocator.get_computers(AgentId("agent2"))[DeviceName("cuda")]
        assert len(agent2_ctx.alloc_map.device_slots) == 1
        assert {d.device_id for d in agent2_ctx.devices} == {DeviceId("cuda3")}

        # Agent3 gets 1 device
        agent3_ctx = allocator.get_computers(AgentId("agent3"))[DeviceName("cuda")]
        assert len(agent3_ctx.alloc_map.device_slots) == 1
        assert {d.device_id for d in agent3_ctx.devices} == {DeviceId("cuda4")}

        await allocator.__aexit__(None, None, None)

    async def test_manual_heterogeneous_shares_non_contiguous(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test MANUAL mode with heterogeneous GPU shares and non-contiguous assignment.

        Setup: 5 GPUs with varying shares, deliberately assigning high-capacity
        GPUs to specific agents:
        - Agent1: cuda0 (2.0) + cuda4 (2.0) = 4.0 shares (non-contiguous high-cap)
        - Agent2: cuda1 (1.0) + cuda3 (1.0) = 2.0 shares (non-contiguous low-cap)
        - Agent3: cuda2 (0.5) = 0.5 shares (single low-cap)
        """
        config = create_manual_multi_agent_config([
            {
                "id": "agent1",
                "cpu": 4,
                "mem": "16G",
                "devices": {"cuda": ["cuda0", "cuda4"]},  # High capacity GPUs
            },
            {
                "id": "agent2",
                "cpu": 2,
                "mem": "8G",
                "devices": {"cuda": ["cuda1", "cuda3"]},  # Medium capacity
            },
            {
                "id": "agent3",
                "cpu": 1,
                "mem": "4G",
                "devices": {"cuda": ["cuda2"]},  # Low capacity
            },
        ])

        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId(f"cpu{i}"): (SlotName("cpu"), Decimal("1")) for i in range(8)
            }),
            DeviceName("mem"): create_fraction_alloc_map({
                DeviceId("root"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("32G"))),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("2.0")),
                DeviceId("cuda1"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda2"): (SlotName("cuda.shares"), Decimal("0.5")),
                DeviceId("cuda3"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda4"): (SlotName("cuda.shares"), Decimal("2.0")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # Agent1 gets high-capacity GPUs (cuda0 + cuda4 = 4.0 shares)
        agent1_ctx = allocator.get_computers(AgentId("agent1"))[DeviceName("cuda")]
        agent1_slots = agent1_ctx.alloc_map.device_slots
        assert {d.device_id for d in agent1_ctx.devices} == {
            DeviceId("cuda0"),
            DeviceId("cuda4"),
        }
        assert agent1_slots[DeviceId("cuda0")].amount == Decimal("2.0")
        assert agent1_slots[DeviceId("cuda4")].amount == Decimal("2.0")

        # Agent2 gets medium GPUs (cuda1 + cuda3 = 2.0 shares)
        agent2_ctx = allocator.get_computers(AgentId("agent2"))[DeviceName("cuda")]
        agent2_slots = agent2_ctx.alloc_map.device_slots
        assert {d.device_id for d in agent2_ctx.devices} == {
            DeviceId("cuda1"),
            DeviceId("cuda3"),
        }
        assert agent2_slots[DeviceId("cuda1")].amount == Decimal("1.0")
        assert agent2_slots[DeviceId("cuda3")].amount == Decimal("1.0")

        # Agent3 gets low-capacity GPU (cuda2 = 0.5 shares)
        agent3_ctx = allocator.get_computers(AgentId("agent3"))[DeviceName("cuda")]
        agent3_slots = agent3_ctx.alloc_map.device_slots
        assert {d.device_id for d in agent3_ctx.devices} == {DeviceId("cuda2")}
        assert agent3_slots[DeviceId("cuda2")].amount == Decimal("0.5")

        await allocator.__aexit__(None, None, None)
