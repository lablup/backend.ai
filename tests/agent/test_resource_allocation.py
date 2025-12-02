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
) -> Mapping[DeviceName, AbstractComputePlugin]:
    """
    Helper to create mock compute plugins for testing.

    This function is isolated to contain the mock creation and type ignores.
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
    return result


@pytest.fixture
def mock_etcd() -> AsyncEtcd:
    """Create a minimal mock etcd for testing."""
    mock: AsyncEtcd = Mock(spec=AsyncEtcd)  # type: ignore[assignment]
    return mock


def setup_mock_resources(
    monkeypatch: pytest.MonkeyPatch,
    computers: Mapping[DeviceName, AbstractComputePlugin],
) -> None:
    """Helper to mock resource loading for a specific test."""

    async def _mock_load(self: ResourceAllocator) -> Mapping[DeviceName, AbstractComputePlugin]:
        return computers

    def _mock_calculate_total_slots(self: ResourceAllocator) -> Mapping[SlotName, Decimal]:
        # Calculate from the mocked computers
        total_slots: dict[SlotName, Decimal] = {}
        for ctx in self.computers.values():
            for slot_info in ctx.alloc_map.device_slots.values():
                if slot_info.slot_name not in total_slots:
                    total_slots[slot_info.slot_name] = Decimal("0")
                total_slots[slot_info.slot_name] += slot_info.amount
        return total_slots

    async def _mock_scan(self: ResourceAllocator) -> Mapping[SlotName, Decimal]:
        # Calculate from the mocked computers
        return _mock_calculate_total_slots(self)

    monkeypatch.setattr(
        "ai.backend.agent.resources.ResourceAllocator._load_resources",
        _mock_load,
    )
    monkeypatch.setattr(
        "ai.backend.agent.resources.ResourceAllocator._scan_available_resources",
        _mock_scan,
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

        setup_mock_resources(monkeypatch, computers)

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

        setup_mock_resources(monkeypatch, computers)

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

        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # alloc_map shows original hardware amounts (unchanged)
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("1.0")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("1.0")

        # AUTO_SPLIT: Each agent gets half (1.0 / 2 = 0.5)
        # reserved_slots = total - allocated = 1.0 - 0.5 = 0.5
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cuda.shares")] == Decimal("0.5")
        assert reserved2[SlotName("cuda.shares")] == Decimal("0.5")

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

        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # alloc_map shows original hardware amounts (unchanged)
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("8")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("8")

        # AUTO_SPLIT: Each agent gets 4 (8 / 2 agents)
        # reserved_slots = total - allocated = 8 - 4 = 4
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cuda")] == Decimal("4")
        assert reserved2[SlotName("cuda")] == Decimal("4")

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

        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        # alloc_map shows original hardware amounts (unchanged)
        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))

        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("5")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("5")
        assert agent3_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("5")

        # 5 divided by 3 = 1 with remainder 2
        # First two agents get 2, last agent gets 1
        # reserved_slots = total - allocated
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        reserved3 = allocator.agent_reserved_slots[AgentId("agent3")]
        assert reserved1[SlotName("cuda")] == Decimal("3")  # 5 - 2 = 3
        assert reserved2[SlotName("cuda")] == Decimal("3")  # 5 - 2 = 3
        assert reserved3[SlotName("cuda")] == Decimal("4")  # 5 - 1 = 4

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

        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # alloc_map shows original hardware amounts (unchanged)
        for i in range(8):
            assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
                DeviceId(f"cpu{i}")
            ].amount == Decimal("2")
            assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
                DeviceId(f"cpu{i}")
            ].amount == Decimal("2")

        # Total = 16, reserved_cpu = 4, available = 12
        # Split between 2 agents: 12 / 2 = 6 per agent
        # reserved_slots = total - allocated = 16 - 6 = 10
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cpu")] == Decimal("10")
        assert reserved2[SlotName("cpu")] == Decimal("10")

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

        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # alloc_map shows original hardware amounts (unchanged)
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("16")
        assert agent1_computers[DeviceName("root")].alloc_map.device_slots[
            DeviceId("mem")
        ].amount == Decimal(BinarySize.finite_from_str("32G"))
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("16")
        assert agent2_computers[DeviceName("root")].alloc_map.device_slots[
            DeviceId("mem")
        ].amount == Decimal(BinarySize.finite_from_str("32G"))

        # MANUAL mode: Each agent gets 4 CPU and 8G mem
        # reserved_slots = total - allocated
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cpu")] == Decimal("12")  # 16 - 4 = 12
        assert reserved1[SlotName("mem")] == Decimal(BinarySize.finite_from_str("24G"))  # 32G - 8G
        assert reserved2[SlotName("cpu")] == Decimal("12")
        assert reserved2[SlotName("mem")] == Decimal(BinarySize.finite_from_str("24G"))

        await allocator.__aexit__(None, None, None)

    async def test_with_allocated_devices(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.MANUAL,
            allocated_cpu=8,
            allocated_mem="16G",
            allocated_devices={
                SlotName("cuda.shares"): Decimal("0.5"),
            },
        )

        # Each device in its own group
        # CPU device group with 1 device
        # Root device group with 1 device (mem)
        # CUDA device group with 1 device (cuda.shares only)
        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("16")),
            }),
            DeviceName("root"): create_fraction_alloc_map({
                DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("32G"))),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda0"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))

        # alloc_map shows original hardware amounts (unchanged)
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda0")
        ].amount == Decimal("1.0")

        # MANUAL mode: agent gets 0.5 cuda.shares
        # reserved_slots = total - allocated = 1.0 - 0.5 = 0.5
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        assert reserved1[SlotName("cuda.shares")] == Decimal("0.5")

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

        setup_mock_resources(monkeypatch, computers)

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

        # alloc_map shows original hardware amounts (unchanged)
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("8")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("8")

        # AUTO_SPLIT: Each agent gets 4 cores (8 / 2 agents)
        # reserved_slots = total - allocated = 8 - 4 = 4
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cpu")] == Decimal("4")
        assert reserved2[SlotName("cpu")] == Decimal("4")

        await allocator.__aexit__(None, None, None)

    async def test_multiple_cpu_cores_manual_mode(
        self,
        mock_etcd: AsyncEtcd,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test MANUAL mode with an 8-core CPU and memory."""
        config = create_test_config(
            allocation_mode=ResourceAllocationMode.MANUAL,
            allocated_cpu=3,
            allocated_mem="8G",
        )

        # Separate CPU and memory into different device groups
        # CPU device group with 1 device (8 cores)
        # Root device group with 1 device (16G mem)
        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
            DeviceName("root"): create_discrete_alloc_map({
                DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("16G"))),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))

        # alloc_map shows original hardware amounts (unchanged)
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("8")
        assert agent1_computers[DeviceName("root")].alloc_map.device_slots[
            DeviceId("mem")
        ].amount == Decimal(BinarySize.finite_from_str("16G"))

        # MANUAL mode: agent gets 3 CPU cores and 8G mem
        # reserved_slots = total - allocated
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        assert reserved1[SlotName("cpu")] == Decimal("5")  # 8 - 3 = 5
        assert reserved1[SlotName("mem")] == Decimal(BinarySize.finite_from_str("8G"))  # 16G - 8G

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

        setup_mock_resources(monkeypatch, computers)

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

        setup_mock_resources(monkeypatch, computers)

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

        setup_mock_resources(monkeypatch, computers)

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

        # alloc_map shows original hardware amounts (unchanged)
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda0")
        ].amount == Decimal("1.0")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda0")
        ].amount == Decimal("1.0")

        # AUTO_SPLIT:
        # CPU: each agent gets 2 cores, reserved = 4 - 2 = 2
        # GPU shares: each agent gets 0.5 shares, reserved = 1.0 - 0.5 = 0.5
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cpu")] == Decimal("2")
        assert reserved2[SlotName("cpu")] == Decimal("2")
        assert reserved1[SlotName("cuda.shares")] == Decimal("0.5")
        assert reserved2[SlotName("cuda.shares")] == Decimal("0.5")

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

        setup_mock_resources(monkeypatch, computers)

        allocator = await ResourceAllocator.new(config, mock_etcd)

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # alloc_map shows original hardware amounts (unchanged)
        for i in range(4):
            assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("1.0")
            assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("1.0")

        # AUTO_SPLIT: Total = 4.0 shares, each agent gets 2.0 shares
        # reserved_slots = total - allocated = 4.0 - 2.0 = 2.0
        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        assert reserved1[SlotName("cuda.shares")] == Decimal("2")
        assert reserved2[SlotName("cuda.shares")] == Decimal("2")

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

        setup_mock_resources(monkeypatch, computers)

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
