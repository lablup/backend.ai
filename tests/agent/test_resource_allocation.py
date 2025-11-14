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
        mock_plugin.list_devices = AsyncMock(return_value=[])  # type: ignore[attr-defined,method-assign]
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

    async def _mock_scan(self: ResourceAllocator) -> Mapping[SlotName, Decimal]:
        return dict(self.total_slots)

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

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

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

        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
            }),
            DeviceName("root"): create_fraction_alloc_map({
                DeviceId("root"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("16G"))),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        agent1_computers = allocator.get_computers(AgentId("agent1"))

        expected_cpu = Decimal("8") - Decimal("2")
        expected_mem = Decimal(BinarySize.finite_from_str("16G")) - Decimal(
            BinarySize.finite_from_str("4G")
        )

        # In SHARED mode with single agent, resources are reduced by reservation
        assert (
            agent1_computers[DeviceName("cpu")].alloc_map.device_slots[DeviceId("cpu")].amount
            == expected_cpu
        )
        assert (
            agent1_computers[DeviceName("root")].alloc_map.device_slots[DeviceId("root")].amount
            == expected_mem
        )

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

        computers = create_mock_computers({
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda"): (SlotName("cuda.shares"), Decimal("1.0")),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # Each agent gets half
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("0.5")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda")
        ].amount == Decimal("0.5")

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

        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId("cuda"): (SlotName("cuda"), Decimal("8")),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # Each agent gets 4
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

        computers = create_mock_computers({
            DeviceName("cuda"): create_discrete_alloc_map({
                DeviceId("cuda"): (SlotName("cuda"), Decimal("5")),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        # 5 divided by 3 = 1 with remainder 2
        # First two agents get 2, last agent gets 1
        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))

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

        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("16")),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # (16 - 4) / 2 = 6 per agent
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("6")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("6")

        reserved1 = allocator.agent_reserved_slots[AgentId("agent1")]
        reserved2 = allocator.agent_reserved_slots[AgentId("agent2")]
        # Each agent has 6 reserved (6 allocated out of 12 total after reservation)
        assert reserved1[SlotName("cpu")] == Decimal("6")
        assert reserved2[SlotName("cpu")] == Decimal("6")

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

        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("16")),
                DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("32G"))),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # Each agent gets exactly what was allocated
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("mem")
        ].amount == Decimal(BinarySize.finite_from_str("8G"))
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("mem")
        ].amount == Decimal(BinarySize.finite_from_str("8G"))

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
                SlotName("cuda.shares"): Decimal("0.3"),
                SlotName("cuda.mem"): Decimal("8000000000"),
            },
        )

        computers = create_mock_computers({
            DeviceName("cpu"): create_fraction_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("16")),
                DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("32G"))),
            }),
            DeviceName("cuda"): create_fraction_alloc_map({
                DeviceId("cuda.shares"): (SlotName("cuda.shares"), Decimal("1.0")),
                DeviceId("cuda.mem"): (SlotName("cuda.mem"), Decimal("16000000000")),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        agent1_computers = allocator.get_computers(AgentId("agent1"))

        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda.shares")
        ].amount == Decimal("0.3")
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda.mem")
        ].amount == Decimal("8000000000")

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

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        assert allocator.total_slots[SlotName("cpu")] == Decimal("8")

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # Each agent gets 4 cores (8 / 2 agents)
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("4")

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

        # Create 1 CPU device with 8 cores and 1 memory device
        computers = create_mock_computers({
            DeviceName("cpu"): create_discrete_alloc_map({
                DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
                DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("16G"))),
            }),
        })

        setup_mock_resources(monkeypatch, computers)

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        agent1_computers = allocator.get_computers(AgentId("agent1"))

        # CPU device should show the manually allocated amount (3 cores out of 8 available)
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("3")

        # Memory device should be set to allocated amount (8G out of 16G available)
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("mem")
        ].amount == Decimal(BinarySize.finite_from_str("8G"))

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

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        # 4 GPUs × 8GB each = 32GB total VRAM
        assert allocator.total_slots[SlotName("cuda.mem")] == Decimal("32000000000")

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

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))
        agent3_computers = allocator.get_computers(AgentId("agent3"))

        # In SHARED mode, all agents see all devices with full capacity
        for i in range(4):
            assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("4")
            assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("4")
            assert agent3_computers[DeviceName("cuda")].alloc_map.device_slots[
                DeviceId(f"cuda{i}")
            ].amount == Decimal("4")

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

        allocator = ResourceAllocator(config, mock_etcd)
        await allocator.__ainit__()

        assert allocator.total_slots[SlotName("cpu")] == Decimal("4")
        assert allocator.total_slots[SlotName("cuda.shares")] == Decimal("1.0")

        agent1_computers = allocator.get_computers(AgentId("agent1"))
        agent2_computers = allocator.get_computers(AgentId("agent2"))

        # CPU split: each agent gets 2 cores (4 / 2 agents)
        assert agent1_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("2")
        assert agent2_computers[DeviceName("cpu")].alloc_map.device_slots[
            DeviceId("cpu")
        ].amount == Decimal("2")

        # GPU shares split fractionally: each agent gets 0.5 shares
        assert agent1_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda0")
        ].amount == Decimal("0.5")
        assert agent2_computers[DeviceName("cuda")].alloc_map.device_slots[
            DeviceId("cuda0")
        ].amount == Decimal("0.5")

        await allocator.__aexit__(None, None, None)
