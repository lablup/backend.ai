"""
Unit tests for ResourcePartitioner and multi-agent resource allocation.

Tests the ResourcePartitioner implementation that handles SHARED, AUTO_SPLIT, and MANUAL
resource allocation modes for multiple agents running on the same physical host.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from ai.backend.agent.alloc_map import (
    AbstractAllocMap,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    FractionAllocMap,
)
from ai.backend.agent.config.unified import ResourceAllocationMode, ResourceConfig
from ai.backend.agent.resources import ComputerContext, ResourcePartitioner
from ai.backend.common.types import BinarySize, DeviceId, DeviceName, SlotName, SlotTypes

if TYPE_CHECKING:
    from collections.abc import Mapping


@pytest.fixture
def base_resource_config() -> ResourceConfig:
    """Basic resource config with no reserved resources."""
    return ResourceConfig(
        reserved_cpu=0,
        reserved_mem=BinarySize.finite_from_str("0"),
        reserved_disk=BinarySize.finite_from_str("0"),
        allocation_mode=ResourceAllocationMode.SHARED,
    )


def create_mock_computer_context(
    device_name: str,
    alloc_map: AbstractAllocMap,
) -> ComputerContext:
    """Helper to create a mock ComputerContext."""
    mock_instance = Mock()
    mock_instance.get_metadata.return_value = {"slot_name": device_name}
    return ComputerContext(
        instance=mock_instance,
        devices=[],
        alloc_map=alloc_map,
    )


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


class TestSharedMode:
    def test_no_restrictions(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.SHARED

        cpu_alloc_map = create_fraction_alloc_map({
            DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
        })
        cuda_alloc_map = create_fraction_alloc_map({
            DeviceId("cuda"): (SlotName("cuda.shares"), Decimal("1.0")),
        })

        computers = {
            DeviceName("cpu"): create_mock_computer_context("cpu", cpu_alloc_map),
            DeviceName("cuda"): create_mock_computer_context("cuda", cuda_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=2, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        # In SHARED mode, all devices get the full total (all agents share the same resources)
        assert cpu_alloc_map.device_slots[DeviceId("cpu")].amount == Decimal("8")
        assert cuda_alloc_map.device_slots[DeviceId("cuda")].amount == Decimal("1.0")
        assert reserved_slots[SlotName("cpu")] == Decimal("0")
        assert reserved_slots[SlotName("cuda.shares")] == Decimal("0")

    def test_with_reserved_resources(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.SHARED
        base_resource_config.reserved_cpu = 2
        base_resource_config.reserved_mem = BinarySize.finite_from_str("4G")

        cpu_alloc_map = create_fraction_alloc_map({
            DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
        })
        mem_alloc_map = create_fraction_alloc_map({
            DeviceId("root"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("16G"))),
        })

        computers = {
            DeviceName("cpu"): create_mock_computer_context("cpu", cpu_alloc_map),
            DeviceName("root"): create_mock_computer_context("root", mem_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=1, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        expected_cpu = Decimal("8") - Decimal("2")
        expected_mem = Decimal(BinarySize.finite_from_str("16G")) - Decimal(
            BinarySize.finite_from_str("4G")
        )

        # In SHARED mode, all CPU devices get the total after reservation (6 CPUs total)
        assert cpu_alloc_map.device_slots[DeviceId("cpu")].amount == expected_cpu
        assert mem_alloc_map.device_slots[DeviceId("root")].amount == expected_mem
        assert reserved_slots[SlotName("cpu")] == Decimal("2")
        assert reserved_slots[SlotName("mem")] == Decimal(BinarySize.finite_from_str("4G"))


class TestAutoSplitMode:
    def test_fraction_alloc_map(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.AUTO_SPLIT

        cuda_alloc_map = create_fraction_alloc_map({
            DeviceId("cuda"): (SlotName("cuda.shares"), Decimal("1.0")),
        })

        computers = {
            DeviceName("cuda"): create_mock_computer_context("cuda", cuda_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=2, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        assert cuda_alloc_map.device_slots[DeviceId("cuda")].amount == Decimal("0.5")
        assert reserved_slots[SlotName("cuda.shares")] == Decimal("0.5")

    def test_discrete_alloc_map_even(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.AUTO_SPLIT

        gpu_alloc_map = create_discrete_alloc_map({
            DeviceId("cuda"): (SlotName("cuda"), Decimal("8")),
        })

        computers = {
            DeviceName("cuda"): create_mock_computer_context("cuda", gpu_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=2, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        assert gpu_alloc_map.device_slots[DeviceId("cuda")].amount == Decimal("4")
        assert reserved_slots[SlotName("cuda")] == Decimal("4")

    def test_discrete_alloc_map_uneven(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.AUTO_SPLIT

        gpu_alloc_map = create_discrete_alloc_map({
            DeviceId("cuda"): (SlotName("cuda"), Decimal("5")),
        })
        computers = {
            DeviceName("cuda"): create_mock_computer_context("cuda", gpu_alloc_map),
        }
        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)

        splitter_0 = ResourcePartitioner(base_resource_config, num_agents=3, agent_idx=0)
        reserved_0 = splitter_0.restrict_computer_resources(computers, total_slots)
        assert gpu_alloc_map.device_slots[DeviceId("cuda")].amount == Decimal("2")
        assert reserved_0[SlotName("cuda")] == Decimal("3")

        gpu_alloc_map = create_discrete_alloc_map({
            DeviceId("cuda"): (SlotName("cuda"), Decimal("5")),
        })
        computers = {
            DeviceName("cuda"): create_mock_computer_context("cuda", gpu_alloc_map),
        }
        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)

        splitter_1 = ResourcePartitioner(base_resource_config, num_agents=3, agent_idx=1)
        reserved_1 = splitter_1.restrict_computer_resources(computers, total_slots)
        assert gpu_alloc_map.device_slots[DeviceId("cuda")].amount == Decimal("2")
        assert reserved_1[SlotName("cuda")] == Decimal("3")

        gpu_alloc_map = create_discrete_alloc_map({
            DeviceId("cuda"): (SlotName("cuda"), Decimal("5")),
        })
        computers = {
            DeviceName("cuda"): create_mock_computer_context("cuda", gpu_alloc_map),
        }
        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)

        splitter_2 = ResourcePartitioner(base_resource_config, num_agents=3, agent_idx=2)
        reserved_2 = splitter_2.restrict_computer_resources(computers, total_slots)
        assert gpu_alloc_map.device_slots[DeviceId("cuda")].amount == Decimal("1")
        assert reserved_2[SlotName("cuda")] == Decimal("4")

    def test_with_reserved_resources(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.AUTO_SPLIT
        base_resource_config.reserved_cpu = 4

        cpu_alloc_map = create_fraction_alloc_map({
            DeviceId("cpu"): (SlotName("cpu"), Decimal("16")),
        })

        computers = {
            DeviceName("cpu"): create_mock_computer_context("cpu", cpu_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=2, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        assert cpu_alloc_map.device_slots[DeviceId("cpu")].amount == Decimal("6")
        assert reserved_slots[SlotName("cpu")] == Decimal("10")

    def test_single_agent_gets_all_resources(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.AUTO_SPLIT
        base_resource_config.reserved_cpu = 2

        cpu_alloc_map = create_fraction_alloc_map({
            DeviceId("cpu"): (SlotName("cpu"), Decimal("16")),
        })

        computers = {
            DeviceName("cpu"): create_mock_computer_context("cpu", cpu_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=1, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        assert cpu_alloc_map.device_slots[DeviceId("cpu")].amount == Decimal("14")
        assert reserved_slots[SlotName("cpu")] == Decimal("2")

    def test_multiple_device_contexts(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.AUTO_SPLIT

        cpu_alloc_map = create_fraction_alloc_map({
            DeviceId("cpu"): (SlotName("cpu"), Decimal("16")),
            DeviceId("mem"): (SlotName("mem"), Decimal(str(64 * 1024**3))),
        })

        cuda_alloc_map = create_fraction_alloc_map({
            DeviceId("cuda"): (SlotName("cuda.shares"), Decimal("1.0")),
        })

        computers = {
            DeviceName("cpu"): create_mock_computer_context("cpu", cpu_alloc_map),
            DeviceName("cuda"): create_mock_computer_context("cuda", cuda_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=3, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        assert cpu_alloc_map.device_slots[DeviceId("cpu")].amount == Decimal("16") / 3
        assert cpu_alloc_map.device_slots[DeviceId("mem")].amount == Decimal(str(64 * 1024**3)) / 3
        assert cuda_alloc_map.device_slots[DeviceId("cuda")].amount == Decimal("1.0") / 3
        assert SlotName("cpu") in reserved_slots
        assert SlotName("mem") in reserved_slots
        assert SlotName("cuda.shares") in reserved_slots

    def test_reserved_slots_accumulate_across_devices(
        self, base_resource_config: ResourceConfig
    ) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.AUTO_SPLIT

        cpu_alloc_map = create_fraction_alloc_map({
            DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
        })

        computers = {
            DeviceName("cpu"): create_mock_computer_context("cpu", cpu_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=2, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        assert cpu_alloc_map.device_slots[DeviceId("cpu")].amount == Decimal("4")
        assert reserved_slots[SlotName("cpu")] == Decimal("4")

    def test_nonzero_reserved_resources(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.AUTO_SPLIT
        base_resource_config.reserved_cpu = 2

        cpu_alloc_map = create_fraction_alloc_map({
            DeviceId("cpu"): (SlotName("cpu"), Decimal("8")),
        })

        computers = {
            DeviceName("cpu"): create_mock_computer_context("cpu", cpu_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=2, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        assert cpu_alloc_map.device_slots[DeviceId("cpu")].amount == Decimal("3")
        assert reserved_slots[SlotName("cpu")] == Decimal("5")

    def test_unrecognized_alloc_map_type_raises_error(
        self, base_resource_config: ResourceConfig
    ) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.AUTO_SPLIT

        class CustomAllocMap(AbstractAllocMap):
            def allocate(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                raise NotImplementedError

            def apply_allocation(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                raise NotImplementedError

            def free(self, *args, **kwargs):  # type: ignore[no-untyped-def]
                raise NotImplementedError

        custom_alloc_map = CustomAllocMap(
            device_slots={
                DeviceId("custom0"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("custom"),
                    amount=Decimal("100"),
                )
            },
            exclusive_slot_types=set(),
        )

        computers = {
            DeviceName("custom"): create_mock_computer_context("custom", custom_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=2, agent_idx=0)

        with pytest.raises(NotImplementedError, match="Unrecognized AbstractAllocMap type"):
            splitter.restrict_computer_resources(computers, total_slots)


class TestManualMode:
    def test_cpu_mem_disk(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.MANUAL
        base_resource_config.allocated_cpu = 4
        base_resource_config.allocated_mem = BinarySize.finite_from_str("8G")
        base_resource_config.allocated_disk = BinarySize.finite_from_str("100G")

        cpu_alloc_map = create_fraction_alloc_map({
            DeviceId("cpu"): (SlotName("cpu"), Decimal("16")),
            DeviceId("mem"): (SlotName("mem"), Decimal(BinarySize.finite_from_str("32G"))),
            DeviceId("disk"): (SlotName("disk"), Decimal(BinarySize.finite_from_str("500G"))),
        })

        computers = {
            DeviceName("cpu"): create_mock_computer_context("cpu", cpu_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=2, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        assert cpu_alloc_map.device_slots[DeviceId("cpu")].amount == Decimal("4")
        assert cpu_alloc_map.device_slots[DeviceId("mem")].amount == Decimal(
            BinarySize.finite_from_str("8G")
        )
        assert cpu_alloc_map.device_slots[DeviceId("disk")].amount == Decimal(
            BinarySize.finite_from_str("100G")
        )
        assert reserved_slots[SlotName("cpu")] == Decimal("12")
        assert reserved_slots[SlotName("mem")] == Decimal(BinarySize.finite_from_str("24G"))
        assert reserved_slots[SlotName("disk")] == Decimal(BinarySize.finite_from_str("400G"))

    def test_with_allocated_devices(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.MANUAL
        base_resource_config.allocated_cpu = 8
        base_resource_config.allocated_mem = BinarySize.finite_from_str("16G")
        base_resource_config.allocated_disk = BinarySize.finite_from_str("200G")
        base_resource_config.allocated_devices = {
            SlotName("cuda.shares"): Decimal("0.3"),
            SlotName("cuda.mem"): Decimal("8000000000"),
        }

        cuda_alloc_map = create_fraction_alloc_map({
            DeviceId("cuda.shares"): (SlotName("cuda.shares"), Decimal("1.0")),
            DeviceId("cuda.mem"): (SlotName("cuda.mem"), Decimal("16000000000")),
        })

        computers = {
            DeviceName("cuda"): create_mock_computer_context("cuda", cuda_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=1, agent_idx=0)
        reserved_slots = splitter.restrict_computer_resources(computers, total_slots)

        assert cuda_alloc_map.device_slots[DeviceId("cuda.shares")].amount == Decimal("0.3")
        assert cuda_alloc_map.device_slots[DeviceId("cuda.mem")].amount == Decimal("8000000000")
        assert reserved_slots[SlotName("cuda.shares")] == Decimal("0.7")
        assert reserved_slots[SlotName("cuda.mem")] == Decimal("8000000000")

    def test_missing_device_raises_error(self, base_resource_config: ResourceConfig) -> None:
        base_resource_config.allocation_mode = ResourceAllocationMode.MANUAL
        base_resource_config.allocated_cpu = 4
        base_resource_config.allocated_mem = BinarySize.finite_from_str("8G")
        base_resource_config.allocated_disk = BinarySize.finite_from_str("100G")

        cuda_alloc_map = create_fraction_alloc_map({
            DeviceId("cuda"): (SlotName("cuda.shares"), Decimal("1.0")),
        })

        computers = {
            DeviceName("cuda"): create_mock_computer_context("cuda", cuda_alloc_map),
        }

        total_slots = ResourcePartitioner.calculate_total_slots(computers, base_resource_config)
        splitter = ResourcePartitioner(base_resource_config, num_agents=1, agent_idx=0)

        with pytest.raises(ValueError, match="slot_name.*cuda\\.shares.*not found"):
            splitter.restrict_computer_resources(computers, total_slots)
