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
    _combine_mappings,
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

        # Create mock devices for each device_id in the alloc_map
        mock_devices: list[AbstractComputeDevice] = []
        for dev_id in alloc_map.device_slots.keys():
            mock_device: AbstractComputeDevice = Mock(spec=AbstractComputeDevice)  # type: ignore[assignment]
            mock_device.device_id = dev_id  # type: ignore[attr-defined]
            mock_devices.append(mock_device)

        # Create a fresh alloc_map for each call
        async def _create_alloc_map(original_map: AbstractAllocMap = alloc_map) -> AbstractAllocMap:  # type: ignore[misc]
            if isinstance(original_map, FractionAllocMap):
                return create_fraction_alloc_map({
                    dev_id: (slot.slot_name, slot.amount)
                    for dev_id, slot in original_map.device_slots.items()
                })
            elif isinstance(original_map, DiscretePropertyAllocMap):
                return create_discrete_alloc_map({
                    dev_id: (slot.slot_name, slot.amount)
                    for dev_id, slot in original_map.device_slots.items()
                })
            raise NotImplementedError(f"Unsupported alloc_map type: {type(original_map)}")

        mock_plugin.create_alloc_map = _create_alloc_map  # type: ignore[attr-defined,assignment]
        mock_plugin.list_devices = AsyncMock(return_value=mock_devices)  # type: ignore[attr-defined,method-assign]
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

    def _mock_calculate_total_slots(self: ResourceAllocator) -> Mapping[SlotName, Decimal]:
        # Calculate from self.computers (set after _create_global_computers)
        total_slots: dict[SlotName, Decimal] = {}
        for ctx in self.computers.values():
            for slot_info in ctx.alloc_map.device_slots.values():
                if slot_info.slot_name not in total_slots:
                    total_slots[slot_info.slot_name] = Decimal("0")
                total_slots[slot_info.slot_name] += slot_info.amount
        return total_slots

    async def _mock_scan(self: ResourceAllocator) -> Mapping[SlotName, Decimal]:
        # Calculate from self.computers
        return _mock_calculate_total_slots(self)

    # Pre-calculate total slots from the spec (before self.computers is set)
    def _mock_calculate_total_slots_from_spec(
        self: ResourceAllocator,  # noqa: ARG001
    ) -> Mapping[SlotName, Decimal]:
        total_slots: dict[SlotName, Decimal] = {}
        for alloc_map in computers_spec.values():
            for slot_info in alloc_map.device_slots.values():
                if slot_info.slot_name not in total_slots:
                    total_slots[slot_info.slot_name] = Decimal("0")
                total_slots[slot_info.slot_name] += slot_info.amount
        return total_slots

    # Mock _calculate_agent_partition to work without self.computers by using spec
    async def _mock_calculate_agent_partition(
        self: ResourceAllocator,
        agent_idx: int,
        agent_config: AgentUnifiedConfig,
        total_slots: Mapping[SlotName, Decimal],
    ) -> tuple[Mapping[SlotName, Decimal], Mapping[SlotName, Decimal], Mapping[SlotName, Decimal]]:
        devices_allocated_slots: list[Mapping[SlotName, Decimal]] = []
        devices_reserved_slots: list[Mapping[SlotName, Decimal]] = []

        for alloc_map in computers_spec.values():
            device_allocated_slots = self._calculate_device_slots(
                alloc_map, agent_idx, agent_config
            )
            devices_allocated_slots.append(device_allocated_slots)

            device_reserved_slots = self._calculate_reserved_slots(
                device_allocated_slots, total_slots
            )
            devices_reserved_slots.append(device_reserved_slots)

        allocated_slots = _combine_mappings(devices_allocated_slots)
        reserved_slots = _combine_mappings(devices_reserved_slots)
        resource_scaling_factor = self._calculate_resource_scaling_factor(allocated_slots)

        return allocated_slots, reserved_slots, resource_scaling_factor

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
    monkeypatch.setattr(
        "ai.backend.agent.resources.ResourceAllocator._calculate_agent_partition",
        _mock_calculate_agent_partition,
    )


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
            DeviceName("root"): create_fraction_alloc_map({
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
        assert agent1_computers[DeviceName("root")].alloc_map.device_slots[
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
    async def test_fraction_alloc_map(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )

        # Single CUDA device with 1.0 shares
        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # With fill-from-front, each agent gets their partition amount (0.5) in device_slots
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("0.5")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("0.5")

        await allocator.__aexit__(None, None, None)

    async def test_discrete_alloc_map_even(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )

        # Single CUDA device with 8 slots
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId("cuda"): (SlotName("cuda"), Decimal("8")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # With fill-from-front, each agent gets their partition amount (4) in device_slots
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("4")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("4")

        await allocator.__aexit__(None, None, None)

    async def test_discrete_alloc_map_uneven(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=3,
        )

        # Single CUDA device with 5 slots
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId("cuda"): (SlotName("cuda"), Decimal("5")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))

        # 5 divided by 3 = 1 with remainder 2
        # First two agents get 2, last agent gets 1
        # With fill-from-front partitioning, device_slots show partitioned amounts
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("2")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("2")
        assert agent3_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("1")

        await allocator.__aexit__(None, None, None)

    async def test_with_reserved_resources(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            reserved_cpu=4,
            num_agents=2,
        )

        # 8 CPU devices with 2 cores each (total 16 cores)
        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId(f"cpu{i}"): (SlotName("cpu"), Decimal("2")) for i in range(8)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # Total = 16, reserved_cpu = 4, available = 12
        # Split between 2 agents: 12 / 2 = 6 per agent
        # With fill-from-front, each agent gets 6 cores distributed across devices:
        # Agent1: cpu0 (2) + cpu1 (2) + cpu2 (2) = 6
        # Agent2: cpu3 (2) + cpu4 (2) + cpu5 (2) = 6
        agent1_slots = agent1_computers[DeviceName("cpu")].alloc_map.device_slots
        agent2_slots = agent2_computers[DeviceName("cpu")].alloc_map.device_slots

        agent1_total = sum(s.amount for s in agent1_slots.values())
        agent2_total = sum(s.amount for s in agent2_slots.values())
        assert agent1_total == Decimal("6")
        assert agent2_total == Decimal("6")

        await allocator.__aexit__(None, None, None)


class TestManualMode:
    async def test_cpu_mem(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.MANUAL,
            allocated_cpu=4,
            allocated_mem="8G",
            num_agents=2,
        )

        # Separate CPU and mem devices in different device groups
        # CPU device group with 1 device (16 cores)
        # Root device group with 1 device (32G mem)
        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("16")),
            }),
            DeviceName("root"): create_fraction_alloc_map({
                DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("32G"))),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # MANUAL mode: Each agent gets 4 CPU and 8G mem
        # With fill-from-front, device_slots show partitioned amounts
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")
        assert agent1_computers[DeviceName("root")].alloc_map.device_slots[
            DeviceId("mem")
        ].amount == Decimal(BinarySize.finite_from_str("8G"))
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")
        assert agent2_computers[DeviceName("root")].alloc_map.device_slots[
            DeviceId("mem")
        ].amount == Decimal(BinarySize.finite_from_str("8G"))

        await allocator.__aexit__(None, None, None)


class TestMultiDeviceScenarios:
    """Tests for realistic multi-device scenarios.

    These tests ensure the resource partitioning logic works correctly with:
    - Single devices (CPU with multiple cores, memory pools)
    - Multiple physical devices (multi-GPU systems, NUMA nodes)
    """

    async def test_multiple_cpu_cores_auto_split(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test AUTO_SPLIT with an 8-core CPU (realistic scenario)."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )

        # Create 1 CPU device with 8 cores (realistic: 1 physical CPU chip)
        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # Verify total slots by summing from computers
        total_cpu = sum(
            slot.amount
            for ctx in allocator.computers.values()
            for slot in ctx.alloc_map.device_slots.values()
            if slot.slot_name == SlotName("cpu")
        )
        assert total_cpu == Decimal("8")

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # AUTO_SPLIT: Each agent gets 4 cores (8 / 2 agents)
        # With fill-from-front, device_slots show partitioned amounts
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")

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
        total_cuda_mem = sum(
            slot.amount
            for ctx in allocator.computers.values()
            for slot in ctx.alloc_map.device_slots.values()
            if slot.slot_name == SlotName("cuda.mem")
        )
        assert total_cuda_mem == Decimal("32000000000")

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
        # Total = 4, with 4 devices, amount per device = 4 / 4 = 1
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

    async def test_mixed_devices_with_different_slot_types(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test with CPU and GPU devices using AUTO_SPLIT.

        CPUs use DiscretePropertyAllocMap, and GPUs with shares use FractionAllocMap.
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )

        # 1 CPU device with 4 cores (discrete)
        # 1 GPU device with fractional shares
        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("4")),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # Verify total slots by summing from computers
        total_cpu = sum(
            slot.amount
            for ctx in allocator.computers.values()
            for slot in ctx.alloc_map.device_slots.values()
            if slot.slot_name == SlotName("cpu")
        )
        total_cuda_shares = sum(
            slot.amount
            for ctx in allocator.computers.values()
            for slot in ctx.alloc_map.device_slots.values()
            if slot.slot_name == SlotName("cuda.shares")
        )
        assert total_cpu == Decimal("4")
        assert total_cuda_shares == Decimal("1.0")

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # AUTO_SPLIT: each agent gets half of resources
        # With fill-from-front, device_slots show partitioned amounts
        # CPU: each agent gets 2 cores
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("2")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("2")

        # GPU shares: each agent gets 0.5 shares
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda0")
        ].amount == Decimal("0.5")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda0")
        ].amount == Decimal("0.5")

        await allocator.__aexit__(None, None, None)

    async def test_multi_gpu_auto_split(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test AUTO_SPLIT with multiple GPU devices sharing the same slot type."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            num_agents=2,
        )

        # 4 GPU devices with 1.0 shares each (total 4.0 shares)
        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.shares"), Decimal("1.0")) for i in range(4)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # AUTO_SPLIT with 4 GPUs: each agent gets 2.0 shares
        # With fill-from-front:
        # Agent1 gets: cuda0 (1.0) + cuda1 (1.0) = 2.0
        # Agent2 gets: cuda2 (1.0) + cuda3 (1.0) = 2.0
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

        await allocator.__aexit__(None, None, None)

    async def test_multi_gpu_shared_mode_with_reservation(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test SHARED mode with multiple GPU devices and system reservation."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.SHARED,
            num_agents=2,
        )

        # 4 GPU devices with 8GB memory each (total 32GB)
        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId(f"cuda{i}"): (SlotName("cuda.mem"), Decimal("8000000000"))
                for i in range(4)
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # SHARED mode: both agents get full resources
        # Total = 32GB, with 4 devices, per-device = 32GB / 4 = 8GB
        for i in range(4):
            assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("8000000000")
            assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("8000000000")

        await allocator.__aexit__(None, None, None)

    async def test_heterogeneous_gpu_fill_from_front(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test fill-from-front with 4 GPUs having different capacities.

        Example from plan: 4 GPUs with shares [3, 2, 2, 3], 3 agents want [4, 4, 2]
        - Agent1: device0 fully (3) + device1 partially (1) = 4
        - Agent2: device1 remainder (1) + device2 fully (2) + device3 partially (1) = 4
        - Agent3: device3 remainder (2) = 2
        """
        # Create a config with 3 agents using MANUAL mode with different allocations
        config = AgentUnifiedConfig.model_validate({
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
                "reserved_cpu": 0,
                "reserved_mem": BinarySize.finite_from_str("0"),
                "reserved_disk": BinarySize.finite_from_str("0"),
                "allocation_mode": ResourceAllocationMode.MANUAL,
            },
            "etcd": {
                "addr": "127.0.0.1:2379",
                "namespace": "test",
            },
            "agents": [
                {
                    "agent": {"id": "agent1"},
                    "resource": {
                        "cpu": 1,
                        "mem": BinarySize.finite_from_str("1G"),
                        "devices": {SlotName("cuda.shares"): Decimal("4")},
                    },
                },
                {
                    "agent": {"id": "agent2"},
                    "resource": {
                        "cpu": 1,
                        "mem": BinarySize.finite_from_str("1G"),
                        "devices": {SlotName("cuda.shares"): Decimal("4")},
                    },
                },
                {
                    "agent": {"id": "agent3"},
                    "resource": {
                        "cpu": 1,
                        "mem": BinarySize.finite_from_str("1G"),
                        "devices": {SlotName("cuda.shares"): Decimal("2")},
                    },
                },
            ],
        })

        # 4 GPU devices with heterogeneous capacities: [3, 2, 2, 3] = 10 total
        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
            DeviceName("root"): create_fraction_alloc_map({
                DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("16G"))),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("3")),
                DeviceId("cuda1"): (SlotName("cuda.shares"), Decimal("2")),
                DeviceId("cuda2"): (SlotName("cuda.shares"), Decimal("2")),
                DeviceId("cuda3"): (SlotName("cuda.shares"), Decimal("3")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))

        # Agent1 should get: cuda0 (full 3) + cuda1 (partial 1) = 4
        agent1_cuda_ctx = agent1_computers[DeviceName("cuda")]
        agent1_cuda = agent1_cuda_ctx.alloc_map.device_slots
        assert DeviceId("cuda0") in agent1_cuda
        assert agent1_cuda[DeviceId("cuda0")].amount == Decimal("3")
        assert DeviceId("cuda1") in agent1_cuda
        assert agent1_cuda[DeviceId("cuda1")].amount == Decimal("1")
        assert len(agent1_cuda) == 2  # Only cuda0 and cuda1
        # Verify device list matches
        agent1_device_ids = {d.device_id for d in agent1_cuda_ctx.devices}
        assert agent1_device_ids == {DeviceId("cuda0"), DeviceId("cuda1")}

        # Agent2 should get: cuda1 (remaining 1) + cuda2 (full 2) + cuda3 (partial 1) = 4
        agent2_cuda_ctx = agent2_computers[DeviceName("cuda")]
        agent2_cuda = agent2_cuda_ctx.alloc_map.device_slots
        assert DeviceId("cuda1") in agent2_cuda
        assert agent2_cuda[DeviceId("cuda1")].amount == Decimal("1")
        assert DeviceId("cuda2") in agent2_cuda
        assert agent2_cuda[DeviceId("cuda2")].amount == Decimal("2")
        assert DeviceId("cuda3") in agent2_cuda
        assert agent2_cuda[DeviceId("cuda3")].amount == Decimal("1")
        assert len(agent2_cuda) == 3  # cuda1, cuda2, cuda3
        # Verify device list matches
        agent2_device_ids = {d.device_id for d in agent2_cuda_ctx.devices}
        assert agent2_device_ids == {DeviceId("cuda1"), DeviceId("cuda2"), DeviceId("cuda3")}

        # Agent3 should get: cuda3 (remaining 2) = 2
        agent3_cuda_ctx = agent3_computers[DeviceName("cuda")]
        agent3_cuda = agent3_cuda_ctx.alloc_map.device_slots
        assert DeviceId("cuda3") in agent3_cuda
        assert agent3_cuda[DeviceId("cuda3")].amount == Decimal("2")
        assert len(agent3_cuda) == 1  # Only cuda3
        # Verify device list matches
        agent3_device_ids = {d.device_id for d in agent3_cuda_ctx.devices}
        assert agent3_device_ids == {DeviceId("cuda3")}

        await allocator.__aexit__(None, None, None)

    async def test_fill_from_front_first_agent_consumes_device(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test when first agent fully consumes a device, second agent starts from next.

        2 GPUs with [2, 2], 2 agents want [2, 2]
        - Agent1: cuda0 fully (2) = 2
        - Agent2: cuda1 fully (2) = 2
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.MANUAL,
            allocated_cpu=1,
            allocated_mem="1G",
            allocated_devices={SlotName("cuda.shares"): Decimal("2")},
            num_agents=2,
        )

        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
            DeviceName("root"): create_fraction_alloc_map({
                DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("16G"))),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("2")),
                DeviceId("cuda1"): (SlotName("cuda.shares"), Decimal("2")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_ctx = allocator.get_computers(AgentId("agent1"))[DeviceName("cuda")]
        agent2_ctx = allocator.get_computers(AgentId("agent2"))[DeviceName("cuda")]

        # Agent1 gets only cuda0
        assert {d.device_id for d in agent1_ctx.devices} == {DeviceId("cuda0")}
        assert agent1_ctx.alloc_map.device_slots[DeviceId("cuda0")].amount == Decimal("2")
        assert len(agent1_ctx.alloc_map.device_slots) == 1

        # Agent2 gets only cuda1
        assert {d.device_id for d in agent2_ctx.devices} == {DeviceId("cuda1")}
        assert agent2_ctx.alloc_map.device_slots[DeviceId("cuda1")].amount == Decimal("2")
        assert len(agent2_ctx.alloc_map.device_slots) == 1

        await allocator.__aexit__(None, None, None)

    async def test_fill_from_front_all_agents_share_one_device(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test when all agents share a single large device.

        1 GPU with capacity 3, 3 agents want [1, 1, 1]
        - Agent1: cuda0 partial (1)
        - Agent2: cuda0 partial (1)
        - Agent3: cuda0 partial (1)
        """
        config = AgentUnifiedConfig.model_validate({
            "agent": {
                "id": "agent1",
                "region": "local",
                "scaling_group": "default",
                "backend": "dummy",
                "rpc_listen_addr": "127.0.0.1:6001",
            },
            "container": {"scratch_type": "hostdir", "stats_type": "docker"},
            "resource": {
                "reserved_cpu": 0,
                "reserved_mem": BinarySize.finite_from_str("0"),
                "reserved_disk": BinarySize.finite_from_str("0"),
                "allocation_mode": ResourceAllocationMode.MANUAL,
            },
            "etcd": {"addr": "127.0.0.1:2379", "namespace": "test"},
            "agents": [
                {
                    "agent": {"id": f"agent{i}"},
                    "resource": {
                        "cpu": 1,
                        "mem": BinarySize.finite_from_str("1G"),
                        "devices": {SlotName("cuda.shares"): Decimal("1")},
                    },
                }
                for i in range(1, 4)
            ],
        })

        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
            DeviceName("root"): create_fraction_alloc_map({
                DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("16G"))),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("3")),
            }),
        })

        setup_mock_resources(monkeypatch, *computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # All 3 agents should share cuda0
        for i in range(1, 4):
            ctx = allocator.get_computers(AgentId(f"agent{i}"))[DeviceName("cuda")]
            assert {d.device_id for d in ctx.devices} == {DeviceId("cuda0")}
            assert ctx.alloc_map.device_slots[DeviceId("cuda0")].amount == Decimal("1")

        await allocator.__aexit__(None, None, None)

    async def test_fill_from_front_discrete_cpu_cores(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """
        Test fill-from-front with discrete CPU cores across multiple CPU devices.

        4 CPU devices with [2, 2, 2, 2] cores, 2 agents want [3, 3]
        - Agent1: cpu0 fully (2) + cpu1 partial (1) = 3
        - Agent2: cpu1 remaining (1) + cpu2 fully (2) = 3
        Reserved cores (2) stay at the end (cpu3).
        """
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.AUTO_SPLIT,
            reserved_cpu=2,
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

        # Agent1: cpu0 (2) + cpu1 (1) = 3
        agent1_slots = agent1_ctx.alloc_map.device_slots
        assert agent1_slots[DeviceId("cpu0")].amount == Decimal("2")
        assert agent1_slots[DeviceId("cpu1")].amount == Decimal("1")
        assert {d.device_id for d in agent1_ctx.devices} == {DeviceId("cpu0"), DeviceId("cpu1")}

        # Agent2: cpu1 (1) + cpu2 (2) = 3
        agent2_slots = agent2_ctx.alloc_map.device_slots
        assert agent2_slots[DeviceId("cpu1")].amount == Decimal("1")
        assert agent2_slots[DeviceId("cpu2")].amount == Decimal("2")
        assert {d.device_id for d in agent2_ctx.devices} == {DeviceId("cpu1"), DeviceId("cpu2")}

        # cpu3 is reserved (not assigned to any agent)

        await allocator.__aexit__(None, None, None)
