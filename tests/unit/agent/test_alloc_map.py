import math
import random
from dataclasses import dataclass
from decimal import ROUND_DOWN, Decimal

import attrs
import pytest

from ai.backend.agent.alloc_map import (
    AllocationStrategy,
    DeviceSlotInfo,
    DiscretePropertyAllocMap,
    FractionAllocMap,
    round_down,
)
from ai.backend.agent.exception import (
    FractionalResourceFragmented,
    InsufficientResource,
    InvalidResourceArgument,
    InvalidResourceCombination,
    NotMultipleOfQuantum,
)
from ai.backend.agent.resources import AbstractComputeDevice
from ai.backend.common.types import DeviceId, SlotName, SlotTypes


@attrs.define(frozen=True, auto_attribs=True)
class DummyDevice(AbstractComputeDevice):
    pass


@pytest.mark.parametrize("alloc_strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
def test_discrete_alloc_map(alloc_strategy: AllocationStrategy) -> None:
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
        },
        allocation_strategy=alloc_strategy,
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0

    result = alloc_map.allocate({
        SlotName("x"): Decimal("1"),
    })
    assert result[SlotName("x")][DeviceId("a0")] == 1
    assert DeviceId("a1") not in result[SlotName("x")]
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 1
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0

    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("x"): Decimal("3"),
        })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 1
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0

    alloc_map.free(result)
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0


def test_discrete_alloc_map_large_number_fill() -> None:
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(100)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(100)),
        },
        allocation_strategy=AllocationStrategy.FILL,
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0

    result = alloc_map.allocate({
        SlotName("x"): Decimal("130"),
    })
    assert result[SlotName("x")][DeviceId("a0")] == 100
    assert result[SlotName("x")][DeviceId("a1")] == 30
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 100
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 30

    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("x"): Decimal("71"),
        })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 100
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 30

    alloc_map.free(result)
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0


def test_discrete_alloc_map_large_number_even() -> None:
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(100)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(100)),
        },
        allocation_strategy=AllocationStrategy.EVENLY,
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0

    result1 = alloc_map.allocate({
        SlotName("x"): Decimal("130"),
    })
    assert result1[SlotName("x")][DeviceId("a0")] == 65
    assert result1[SlotName("x")][DeviceId("a1")] == 65
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 65
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 65

    result2 = alloc_map.allocate({
        SlotName("x"): Decimal("15"),
    })
    assert result2[SlotName("x")][DeviceId("a0")] == 8
    assert result2[SlotName("x")][DeviceId("a1")] == 7
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 73
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 72

    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("x"): Decimal("99"),
        })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 73
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 72

    alloc_map.free(result1)
    alloc_map.free(result2)
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0


def test_discrete_alloc_map_even_to_tightly_fill() -> None:
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(10)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(10)),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(10)),
        },
        allocation_strategy=AllocationStrategy.EVENLY,
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == 0

    result1 = alloc_map.allocate({
        SlotName("x"): Decimal("7"),
    })
    assert result1[SlotName("x")][DeviceId("a0")] == 3
    assert result1[SlotName("x")][DeviceId("a1")] == 2
    assert result1[SlotName("x")][DeviceId("a2")] == 2
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 3
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 2
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == 2

    result2 = alloc_map.allocate({
        SlotName("x"): Decimal("23"),
    })
    assert result2[SlotName("x")][DeviceId("a0")] == 7
    assert result2[SlotName("x")][DeviceId("a1")] == 8
    assert result2[SlotName("x")][DeviceId("a2")] == 8
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 10
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 10
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == 10

    alloc_map.free(result1)
    alloc_map.free(result2)
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == 0
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == 0


def test_discrete_alloc_map_cpu_even() -> None:
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("cpu0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(2)),
            DeviceId("cpu1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(2)),
            DeviceId("cpu2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(2)),
            DeviceId("cpu3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cpu"), Decimal(2)),
        },
        allocation_strategy=AllocationStrategy.EVENLY,
    )

    def check_clean() -> None:
        assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu0")] == 0
        assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu1")] == 0
        assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu2")] == 0
        assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu3")] == 0

    check_clean()

    result1 = alloc_map.allocate({
        SlotName("cpu"): Decimal("4"),
    })
    assert result1[SlotName("cpu")][DeviceId("cpu0")] == 1
    assert result1[SlotName("cpu")][DeviceId("cpu1")] == 1
    assert result1[SlotName("cpu")][DeviceId("cpu2")] == 1
    assert result1[SlotName("cpu")][DeviceId("cpu3")] == 1
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu0")] == 1
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu1")] == 1
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu2")] == 1
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu3")] == 1

    result2 = alloc_map.allocate({
        SlotName("cpu"): Decimal("2"),
    })
    assert result2[SlotName("cpu")][DeviceId("cpu0")] == 1
    assert result2[SlotName("cpu")][DeviceId("cpu1")] == 1
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu0")] == 2
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu1")] == 2
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu2")] == 1
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu3")] == 1

    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("cpu"): Decimal("3"),
        })
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu0")] == 2
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu1")] == 2
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu2")] == 1
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu3")] == 1

    result3 = alloc_map.allocate({
        SlotName("cpu"): Decimal("2"),
    })
    assert result3[SlotName("cpu")][DeviceId("cpu2")] == 1
    assert result3[SlotName("cpu")][DeviceId("cpu3")] == 1
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu0")] == 2
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu1")] == 2
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu2")] == 2
    assert alloc_map.allocations[SlotName("cpu")][DeviceId("cpu3")] == 2

    alloc_map.free(result1)
    alloc_map.free(result2)
    alloc_map.free(result3)
    check_clean()


def test_fraction_alloc_map() -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
        },
        allocation_strategy=AllocationStrategy.FILL,
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0")

    result = alloc_map.allocate({
        SlotName("x"): Decimal("1.5"),
    })
    assert result[SlotName("x")][DeviceId("a0")] == Decimal("1.0")
    assert result[SlotName("x")][DeviceId("a1")] == Decimal("0.5")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("1.0")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.5")

    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("x"): Decimal("1.5"),
        })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("1.0")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.5")

    alloc_map.free(result)
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0")


def test_fraction_alloc_map_many_device() -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a4"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a5"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a6"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a7"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
        },
        allocation_strategy=AllocationStrategy.FILL,
    )
    for idx in range(8):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")

    result = alloc_map.allocate({
        SlotName("x"): Decimal("7.95"),
    })
    for idx in range(7):
        assert result[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("1.0")
    assert result[SlotName("x")][DeviceId("a7")] == Decimal("0.95")
    for idx in range(7):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("1.0")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a7")] == Decimal("0.95")

    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("x"): Decimal("1.0"),
        })
    for idx in range(7):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("1.0")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a7")] == Decimal("0.95")

    alloc_map.free(result)
    for idx in range(8):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")


def test_fraction_alloc_map_iteration() -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
        },
        allocation_strategy=AllocationStrategy.FILL,
        quantum_size=Decimal("0.00001"),
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0")

    for _ in range(1000):
        alloc_map.allocate({
            SlotName("x"): Decimal("0.00001"),
        })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.005")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.005")

    alloc_map.free({SlotName("x"): {DeviceId("a0"): Decimal("0.00001")}})
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.00499")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.005")

    for _ in range(499):
        alloc_map.free({SlotName("x"): {DeviceId("a0"): Decimal("0.00001")}})
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.005")


def test_fraction_alloc_map_random_generated_allocations() -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1.0)),
        },
        allocation_strategy=AllocationStrategy.FILL,
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0")

    quantum = Decimal(".01")
    for _ in range(5):
        allocations = []
        for _ in range(10):
            result = alloc_map.allocate({
                SlotName("x"): Decimal(random.uniform(0, 0.1)).quantize(quantum, ROUND_DOWN),
            })
            allocations.append(result)
        assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] >= Decimal("0")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] >= Decimal("0")
        for a in allocations:
            alloc_map.free(a)
        assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0")


def test_fraction_alloc_map_even_allocation() -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.05")),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.1")),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.2")),
            DeviceId("a3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.3")),
            DeviceId("a4"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.0")),
        },
        allocation_strategy=AllocationStrategy.EVENLY,
    )
    assert sum(alloc_map.allocations[SlotName("x")].values(), start=Decimal(0)) == 0

    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("x"): Decimal("0.66"),
        })

    with pytest.raises(InsufficientResource):
        alloc_map.allocate(
            {
                SlotName("x"): Decimal("0.06"),
            },
            min_memory=Decimal(0.6),
        )
    for _ in range(20):
        alloc_map.allocate({
            SlotName("x"): Decimal("0.01"),
        })

    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.05")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.1")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("0.05")
    alloc_map.free({
        SlotName("x"): {
            DeviceId("a0"): Decimal("0.05"),
            DeviceId("a1"): Decimal("0.1"),
            DeviceId("a2"): Decimal("0.05"),
        }
    })
    assert sum(alloc_map.allocations[SlotName("x")].values(), start=Decimal(0)) == 0

    result = alloc_map.allocate({
        SlotName("x"): Decimal("0.2"),
    })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("0.2")

    alloc_map.free(result)
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("0")

    result = alloc_map.allocate(
        {
            SlotName("x"): Decimal("0.2"),
        },
        min_memory=Decimal("0.25"),
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a3")] == Decimal("0.2")
    alloc_map.free(result)
    for idx in range(5):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")

    result = alloc_map.allocate({
        SlotName("x"): Decimal("0.5"),
    })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("0.2")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a3")] == Decimal("0.3")
    alloc_map.free(result)
    for idx in range(5):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")

    result = alloc_map.allocate({
        SlotName("x"): Decimal("0.65"),
    })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.05")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.1")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("0.2")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a3")] == Decimal("0.3")
    alloc_map.free(result)
    for idx in range(5):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")

    result = alloc_map.allocate(
        {
            SlotName("x"): Decimal("0.6"),
        },
        min_memory=Decimal("0.1"),
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.1")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("0.2")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a3")] == Decimal("0.3")
    alloc_map.free(result)
    for idx in range(5):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")

    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.3")),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.3")),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.9")),
        },
    )
    result = alloc_map.allocate({
        SlotName("x"): Decimal("1"),
    })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.3")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.3")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("0.4")


def test_fraction_alloc_map_even_allocation_fractions() -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.8")),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.75")),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.7")),
            DeviceId("a3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.3")),
            DeviceId("a4"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("0.0")),
        },
        allocation_strategy=AllocationStrategy.EVENLY,
    )
    result = alloc_map.allocate({
        SlotName("x"): Decimal("2.31"),
    })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.67")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.67")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("0.67")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a3")] == Decimal("0.3")
    alloc_map.free(result)
    for idx in range(4):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")

    result = alloc_map.allocate({
        SlotName("x"): Decimal("2"),
    })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.67")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.67")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("0.66")
    alloc_map.free(result)
    for idx in range(3):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")


def test_fraction_alloc_map_even_allocation_many_devices() -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(2)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(3)),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(3)),
            DeviceId("a3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(5)),
        },
        allocation_strategy=AllocationStrategy.EVENLY,
    )
    result = alloc_map.allocate({
        SlotName("x"): Decimal("6"),
    })
    assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("3")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a2")] == Decimal("3")
    alloc_map.free(result)
    for idx in range(4):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")

    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.0")),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.5")),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("2.0")),
            DeviceId("a3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("3.0")),
            DeviceId("a4"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("3.0")),
            DeviceId("a5"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("4.0")),
            DeviceId("a6"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("4.5")),
            DeviceId("a7"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("5.0")),
            DeviceId("a8"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("5.0")),
        },
        allocation_strategy=AllocationStrategy.EVENLY,
    )

    result = alloc_map.allocate(
        {
            SlotName("x"): Decimal("6"),
        },
        min_memory=Decimal("2.5"),
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a3")] == Decimal("3")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a4")] == Decimal("3")
    alloc_map.free(result)
    for idx in range(9):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")

    result = alloc_map.allocate(
        {
            SlotName("x"): Decimal("11"),
        },
        min_memory=Decimal("0.84"),
    )
    assert alloc_map.allocations[SlotName("x")][DeviceId("a3")] == Decimal("2.75")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a4")] == Decimal("2.75")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a5")] == Decimal("2.75")
    assert alloc_map.allocations[SlotName("x")][DeviceId("a5")] == Decimal("2.75")
    alloc_map.free(result)
    for idx in range(9):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")


def test_fraction_alloc_map_even_allocation_many_devices_2() -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.0")),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.0")),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.0")),
            DeviceId("a3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.0")),
            DeviceId("a4"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.0")),
            DeviceId("a5"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.0")),
            DeviceId("a6"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.0")),
            DeviceId("a7"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal("1.0")),
        },
        allocation_strategy=AllocationStrategy.EVENLY,
    )
    result = alloc_map.allocate({
        SlotName("x"): Decimal("6"),
    })
    count_0 = 0
    count_1 = 0
    # NOTE: the even allocator favors the tail of device list when it fills up.
    # So we rely on the counting of desire per-device allocations instead of matching
    # the device index and the allocations.
    for idx in range(8):
        if alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("1.0"):
            count_1 += 1
        if alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0"):
            count_0 += 1
    assert count_0 == 2
    assert count_1 == 6
    alloc_map.free(result)
    for idx in range(8):
        assert alloc_map.allocations[SlotName("x")][DeviceId(f"a{idx}")] == Decimal("0")


@pytest.mark.parametrize(
    "alloc_strategy",
    [AllocationStrategy.FILL, AllocationStrategy.EVENLY],
)
def test_quantum_size(alloc_strategy: AllocationStrategy) -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
            DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
        },
        quantum_size=Decimal("0.25"),
        allocation_strategy=alloc_strategy,
    )
    result = alloc_map.allocate({
        SlotName("x"): Decimal("0.5"),
    })
    assert sum(alloc_map.allocations[SlotName("x")].values()) == Decimal("0.5")
    alloc_map.free(result)

    result = alloc_map.allocate({
        SlotName("x"): Decimal("1.5"),
    })
    assert sum(alloc_map.allocations[SlotName("x")].values()) == Decimal("1.5")
    if alloc_strategy == AllocationStrategy.EVENLY:
        assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.75")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.75")
    else:
        assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("1.00")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.50")
    alloc_map.free(result)

    # input is below 0.25
    with pytest.raises(NotMultipleOfQuantum, match="actual calculated amount is zero"):
        alloc_map.allocate({
            SlotName("x"): Decimal("0.24"),
        })

    if alloc_strategy == AllocationStrategy.EVENLY:
        # input IS multiple of 0.25 but the CALCULATED allocations are not multiple of 0.25
        result = alloc_map.allocate({
            SlotName("x"): Decimal("1.75"),  # divided to 0.88 and 0.87
        })
        assert sum(alloc_map.allocations[SlotName("x")].values()) == Decimal("1.5")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.75")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.75")
        alloc_map.free(result)

        # inputs are not multiple of 0.25
        result = alloc_map.allocate({
            SlotName("x"): Decimal("0.52"),
        })
        assert sum(alloc_map.allocations[SlotName("x")].values()) == Decimal("0.5")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.5")
        alloc_map.free(result)

        result = alloc_map.allocate({
            SlotName("x"): Decimal("0.42"),
        })
        assert sum(alloc_map.allocations[SlotName("x")].values()) == Decimal("0.25")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.25")
        alloc_map.free(result)

        with pytest.raises(InsufficientResource):
            alloc_map.allocate({
                SlotName("x"): Decimal("3.99"),
            })
    else:
        # inputs are not multiple of 0.25
        result = alloc_map.allocate({
            SlotName("x"): Decimal("0.52"),
        })
        assert sum(alloc_map.allocations[SlotName("x")].values()) == Decimal("0.5")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.5")
        alloc_map.free(result)

        result = alloc_map.allocate({
            SlotName("x"): Decimal("0.42"),
        })
        assert sum(alloc_map.allocations[SlotName("x")].values()) == Decimal("0.25")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.25")
        alloc_map.free(result)

        with pytest.raises(InsufficientResource):
            alloc_map.allocate({
                SlotName("x"): Decimal("3.99"),
            })
        # In this case, it satisfies the quantum condition, because the capacity of devices are
        # multiples of the quantum.
        alloc_map.allocate({
            SlotName("x"): Decimal("1.75"),
        })
        assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("1.00")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a1")] == Decimal("0.75")

        # So let's change the situation.
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId("a0"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
                DeviceId("a1"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("x"), Decimal(1)),
            },
            quantum_size=Decimal("0.3"),
            allocation_strategy=alloc_strategy,
        )
        result = alloc_map.allocate({
            SlotName("x"): Decimal("0.5"),
        })
        assert sum(alloc_map.allocations[SlotName("x")].values()) == Decimal("0.3")
        assert alloc_map.allocations[SlotName("x")][DeviceId("a0")] == Decimal("0.3")
        alloc_map.free(result)


def test_exclusive_resource_slots() -> None:
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(
                SlotTypes.UNIQUE, SlotName("cuda.device:1g.5gb-mig"), Decimal(1)
            ),
            DeviceId("a1"): DeviceSlotInfo(
                SlotTypes.UNIQUE, SlotName("cuda.device:1g.5gb-mig"), Decimal(1)
            ),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda.device"), Decimal(1)),
            DeviceId("a3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda.device"), Decimal(1)),
            DeviceId("a4"): DeviceSlotInfo(
                SlotTypes.UNIQUE, SlotName("cuda.device:3g.20gb-mig"), Decimal(1)
            ),
        },
        exclusive_slot_types={"cuda.device:*-mig", "cuda.device", "cuda.shares"},
    )

    def check_clean() -> None:
        assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a0")] == Decimal(
            "0"
        )
        assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a1")] == Decimal(
            "0"
        )
        assert alloc_map.allocations[SlotName("cuda.device")][DeviceId("a2")] == Decimal("0")
        assert alloc_map.allocations[SlotName("cuda.device")][DeviceId("a3")] == Decimal("0")
        assert alloc_map.allocations[SlotName("cuda.device:3g.20gb-mig")][
            DeviceId("a4")
        ] == Decimal("0")

    with pytest.raises(InvalidResourceCombination):
        alloc_map.allocate({
            SlotName("cuda.device"): Decimal("2"),
            SlotName("cuda.device:1g.5gb-mig"): Decimal("1"),
        })
    check_clean()


def test_heterogeneous_resource_slots_with_discrete_alloc_map() -> None:
    alloc_map = DiscretePropertyAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(
                SlotTypes.UNIQUE, SlotName("cuda.device:1g.5gb-mig"), Decimal(1)
            ),
            DeviceId("a1"): DeviceSlotInfo(
                SlotTypes.UNIQUE, SlotName("cuda.device:1g.5gb-mig"), Decimal(1)
            ),
            DeviceId("a2"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda.device"), Decimal(1)),
            DeviceId("a3"): DeviceSlotInfo(SlotTypes.COUNT, SlotName("cuda.device"), Decimal(1)),
            DeviceId("a4"): DeviceSlotInfo(
                SlotTypes.UNIQUE, SlotName("cuda.device:3g.20gb-mig"), Decimal(1)
            ),
        },
        exclusive_slot_types={"cuda.device:*-mig", "cuda.device", "cuda.shares"},
    )

    def check_clean() -> None:
        assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a0")] == Decimal(
            "0"
        )
        assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a1")] == Decimal(
            "0"
        )
        assert alloc_map.allocations[SlotName("cuda.device")][DeviceId("a2")] == Decimal("0")
        assert alloc_map.allocations[SlotName("cuda.device")][DeviceId("a3")] == Decimal("0")
        assert alloc_map.allocations[SlotName("cuda.device:3g.20gb-mig")][
            DeviceId("a4")
        ] == Decimal("0")

    check_clean()

    # check allocation of non-unique slots
    result = alloc_map.allocate({
        SlotName("cuda.device"): Decimal("2"),
    })
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a0")] == Decimal("0")
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a1")] == Decimal("0")
    assert alloc_map.allocations[SlotName("cuda.device")][DeviceId("a2")] == Decimal("1")
    assert alloc_map.allocations[SlotName("cuda.device")][DeviceId("a3")] == Decimal("1")
    assert alloc_map.allocations[SlotName("cuda.device:3g.20gb-mig")][DeviceId("a4")] == Decimal(
        "0"
    )
    alloc_map.free(result)
    check_clean()

    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("cuda.device"): Decimal("3"),
        })
    check_clean()

    # allocating zero means no-op.
    alloc_map.allocate({
        SlotName("cuda.device:1g.5gb-mig"): Decimal("0"),
    })
    check_clean()

    # any allocation request for unique slots should specify the amount 1.
    with pytest.raises(InvalidResourceArgument):
        alloc_map.allocate({
            SlotName("cuda.device:1g.5gb-mig"): Decimal("1.1"),
        })
    with pytest.raises(InvalidResourceArgument):
        alloc_map.allocate({
            SlotName("cuda.device:1g.5gb-mig"): Decimal("2"),
        })
    check_clean()

    # test alloaction of unique slots
    result1 = alloc_map.allocate({
        SlotName("cuda.device:1g.5gb-mig"): Decimal("1"),
    })
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a0")] == Decimal("1")
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a1")] == Decimal("0")
    result2 = alloc_map.allocate({
        SlotName("cuda.device:1g.5gb-mig"): Decimal("1"),
    })
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a0")] == Decimal("1")
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a1")] == Decimal("1")
    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("cuda.device:1g.5gb-mig"): Decimal("1"),
        })
    alloc_map.free(result1)
    alloc_map.free(result2)
    check_clean()


def test_heterogeneous_resource_slots_with_fractional_alloc_map() -> None:
    alloc_map = FractionAllocMap(
        device_slots={
            DeviceId("a0"): DeviceSlotInfo(
                SlotTypes.UNIQUE, SlotName("cuda.device:1g.5gb-mig"), Decimal(1)
            ),
            DeviceId("a1"): DeviceSlotInfo(
                SlotTypes.UNIQUE, SlotName("cuda.device:1g.5gb-mig"), Decimal(1)
            ),
            DeviceId("a2"): DeviceSlotInfo(
                SlotTypes.COUNT, SlotName("cuda.shares"), Decimal("1.0")
            ),
            DeviceId("a3"): DeviceSlotInfo(
                SlotTypes.COUNT, SlotName("cuda.shares"), Decimal("1.0")
            ),
            DeviceId("a4"): DeviceSlotInfo(
                SlotTypes.UNIQUE, SlotName("cuda.device:3g.20gb-mig"), Decimal(1)
            ),
        },
        exclusive_slot_types={"cuda.device:*-mig", "cuda.device", "cuda.shares"},
        allocation_strategy=AllocationStrategy.FILL,
    )

    def check_clean() -> None:
        assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a0")] == Decimal(
            "0"
        )
        assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a1")] == Decimal(
            "0"
        )
        assert alloc_map.allocations[SlotName("cuda.shares")][DeviceId("a2")] == Decimal("0")
        assert alloc_map.allocations[SlotName("cuda.shares")][DeviceId("a3")] == Decimal("0")
        assert alloc_map.allocations[SlotName("cuda.device:3g.20gb-mig")][
            DeviceId("a4")
        ] == Decimal("0")

    check_clean()

    # check allocation of non-unique slots
    result = alloc_map.allocate({
        SlotName("cuda.shares"): Decimal("2.0"),
    })
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a0")] == Decimal("0")
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a1")] == Decimal("0")
    assert alloc_map.allocations[SlotName("cuda.shares")][DeviceId("a2")] == Decimal("1.0")
    assert alloc_map.allocations[SlotName("cuda.shares")][DeviceId("a3")] == Decimal("1.0")
    assert alloc_map.allocations[SlotName("cuda.device:3g.20gb-mig")][DeviceId("a4")] == Decimal(
        "0"
    )
    alloc_map.free(result)
    check_clean()

    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("cuda.shares"): Decimal("2.5"),
        })
    check_clean()

    # allocating zero means no-op.
    alloc_map.allocate({
        SlotName("cuda.device:1g.5gb-mig"): Decimal("0"),
    })
    check_clean()

    # any allocation request for unique slots should specify the amount 1.
    with pytest.raises(InvalidResourceArgument):
        alloc_map.allocate({
            SlotName("cuda.device:1g.5gb-mig"): Decimal("0.3"),
        })
    with pytest.raises(InvalidResourceArgument):
        alloc_map.allocate({
            SlotName("cuda.device:1g.5gb-mig"): Decimal("1.5"),
        })
    check_clean()

    # test alloaction of unique slots
    result1 = alloc_map.allocate({
        SlotName("cuda.device:1g.5gb-mig"): Decimal("1"),
    })
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a0")] == Decimal("1")
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a1")] == Decimal("0")
    result2 = alloc_map.allocate({
        SlotName("cuda.device:1g.5gb-mig"): Decimal("1"),
    })
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a0")] == Decimal("1")
    assert alloc_map.allocations[SlotName("cuda.device:1g.5gb-mig")][DeviceId("a1")] == Decimal("1")
    with pytest.raises(InsufficientResource):
        alloc_map.allocate({
            SlotName("cuda.device:1g.5gb-mig"): Decimal("1"),
        })
    alloc_map.free(result1)
    alloc_map.free(result2)
    check_clean()


@dataclass(frozen=True)
class DefragAllocationExpectation:
    """Expected values for anti-fragmentation allocation.

    Attributes:
        requested_resource: Total requested resource amount (e.g. Decimal("1.5"))
        expected_num_devices: Number of devices needed (e.g. 2)
        expected_density: Raw per-device density (e.g. Decimal("0.75"))
        expected_quantized_density: Quantized density (e.g. Decimal("0.8"))
    """

    requested_resource: Decimal
    expected_num_devices: int
    expected_density: Decimal
    expected_quantized_density: Decimal


DEFRAG_ALLOCATION_CASES: list[DefragAllocationExpectation] = [
    # single device - requested=0.1~1.0
    DefragAllocationExpectation(Decimal("0.1"), 1, Decimal("0.1"), Decimal("0.1")),
    DefragAllocationExpectation(Decimal("0.2"), 1, Decimal("0.2"), Decimal("0.2")),
    DefragAllocationExpectation(Decimal("0.3"), 1, Decimal("0.3"), Decimal("0.3")),
    DefragAllocationExpectation(Decimal("0.4"), 1, Decimal("0.4"), Decimal("0.4")),
    DefragAllocationExpectation(Decimal("0.5"), 1, Decimal("0.5"), Decimal("0.5")),
    DefragAllocationExpectation(Decimal("0.6"), 1, Decimal("0.6"), Decimal("0.6")),
    DefragAllocationExpectation(Decimal("0.7"), 1, Decimal("0.7"), Decimal("0.7")),
    DefragAllocationExpectation(Decimal("0.8"), 1, Decimal("0.8"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("0.9"), 1, Decimal("0.9"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("1.0"), 1, Decimal("1.0"), Decimal("1.0")),
    # two devices - requested=1.1~2.0
    DefragAllocationExpectation(Decimal("1.1"), 2, Decimal("0.55"), Decimal("0.5")),
    DefragAllocationExpectation(Decimal("1.2"), 2, Decimal("0.6"), Decimal("0.6")),
    DefragAllocationExpectation(Decimal("1.3"), 2, Decimal("0.65"), Decimal("0.6")),
    DefragAllocationExpectation(Decimal("1.4"), 2, Decimal("0.7"), Decimal("0.7")),
    DefragAllocationExpectation(Decimal("1.5"), 2, Decimal("0.75"), Decimal("0.7")),
    DefragAllocationExpectation(Decimal("1.6"), 2, Decimal("0.8"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("1.7"), 2, Decimal("0.85"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("1.8"), 2, Decimal("0.9"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("1.9"), 2, Decimal("0.95"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("2.0"), 2, Decimal("1.0"), Decimal("1.0")),
    # three devices - requested=2.1~3.0
    DefragAllocationExpectation(Decimal("2.1"), 3, Decimal("0.7"), Decimal("0.7")),
    DefragAllocationExpectation(
        Decimal("2.2"), 3, Decimal("0.7333333333333333333333333333"), Decimal("0.7")
    ),
    DefragAllocationExpectation(
        Decimal("2.3"), 3, Decimal("0.7666666666666666666666666667"), Decimal("0.7")
    ),
    DefragAllocationExpectation(Decimal("2.4"), 3, Decimal("0.8"), Decimal("0.8")),
    DefragAllocationExpectation(
        Decimal("2.5"), 3, Decimal("0.8333333333333333333333333333"), Decimal("0.8")
    ),
    DefragAllocationExpectation(
        Decimal("2.6"), 3, Decimal("0.8666666666666666666666666667"), Decimal("0.8")
    ),
    DefragAllocationExpectation(Decimal("2.7"), 3, Decimal("0.9"), Decimal("0.9")),
    DefragAllocationExpectation(
        Decimal("2.8"), 3, Decimal("0.9333333333333333333333333333"), Decimal("0.9")
    ),
    DefragAllocationExpectation(
        Decimal("2.9"), 3, Decimal("0.9666666666666666666666666667"), Decimal("0.9")
    ),
    DefragAllocationExpectation(Decimal("3.0"), 3, Decimal("1.0"), Decimal("1.0")),
    # four devices - requested=3.1~4.0
    DefragAllocationExpectation(Decimal("3.1"), 4, Decimal("0.775"), Decimal("0.7")),
    DefragAllocationExpectation(Decimal("3.2"), 4, Decimal("0.8"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("3.3"), 4, Decimal("0.825"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("3.4"), 4, Decimal("0.85"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("3.5"), 4, Decimal("0.875"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("3.6"), 4, Decimal("0.9"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("3.7"), 4, Decimal("0.925"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("3.8"), 4, Decimal("0.95"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("3.9"), 4, Decimal("0.975"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("4.0"), 4, Decimal("1.0"), Decimal("1.0")),
    # five devices - requested=4.1~5.0
    DefragAllocationExpectation(Decimal("4.1"), 5, Decimal("0.82"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("4.2"), 5, Decimal("0.84"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("4.3"), 5, Decimal("0.86"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("4.4"), 5, Decimal("0.88"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("4.5"), 5, Decimal("0.9"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("4.6"), 5, Decimal("0.92"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("4.7"), 5, Decimal("0.94"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("4.8"), 5, Decimal("0.96"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("4.9"), 5, Decimal("0.98"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("5.0"), 5, Decimal("1.0"), Decimal("1.0")),
    # six devices - requested=5.1~6.0
    DefragAllocationExpectation(Decimal("5.1"), 6, Decimal("0.85"), Decimal("0.8")),
    DefragAllocationExpectation(
        Decimal("5.2"), 6, Decimal("0.8666666666666666666666666667"), Decimal("0.8")
    ),
    DefragAllocationExpectation(
        Decimal("5.3"), 6, Decimal("0.8833333333333333333333333333"), Decimal("0.8")
    ),
    DefragAllocationExpectation(Decimal("5.4"), 6, Decimal("0.9"), Decimal("0.9")),
    DefragAllocationExpectation(
        Decimal("5.5"), 6, Decimal("0.9166666666666666666666666667"), Decimal("0.9")
    ),
    DefragAllocationExpectation(
        Decimal("5.6"), 6, Decimal("0.9333333333333333333333333333"), Decimal("0.9")
    ),
    DefragAllocationExpectation(Decimal("5.7"), 6, Decimal("0.95"), Decimal("0.9")),
    DefragAllocationExpectation(
        Decimal("5.8"), 6, Decimal("0.9666666666666666666666666667"), Decimal("0.9")
    ),
    DefragAllocationExpectation(
        Decimal("5.9"), 6, Decimal("0.9833333333333333333333333333"), Decimal("0.9")
    ),
    DefragAllocationExpectation(Decimal("6.0"), 6, Decimal("1.0"), Decimal("1.0")),
    # seven devices - requested=6.1~7.0
    DefragAllocationExpectation(
        Decimal("6.1"), 7, Decimal("0.8714285714285714285714285714"), Decimal("0.8")
    ),
    DefragAllocationExpectation(
        Decimal("6.2"), 7, Decimal("0.8857142857142857142857142857"), Decimal("0.8")
    ),
    DefragAllocationExpectation(Decimal("6.3"), 7, Decimal("0.9"), Decimal("0.9")),
    DefragAllocationExpectation(
        Decimal("6.4"), 7, Decimal("0.9142857142857142857142857143"), Decimal("0.9")
    ),
    DefragAllocationExpectation(
        Decimal("6.5"), 7, Decimal("0.9285714285714285714285714286"), Decimal("0.9")
    ),
    DefragAllocationExpectation(
        Decimal("6.6"), 7, Decimal("0.9428571428571428571428571429"), Decimal("0.9")
    ),
    DefragAllocationExpectation(
        Decimal("6.7"), 7, Decimal("0.9571428571428571428571428571"), Decimal("0.9")
    ),
    DefragAllocationExpectation(
        Decimal("6.8"), 7, Decimal("0.9714285714285714285714285714"), Decimal("0.9")
    ),
    DefragAllocationExpectation(
        Decimal("6.9"), 7, Decimal("0.9857142857142857142857142857"), Decimal("0.9")
    ),
    DefragAllocationExpectation(Decimal("7.0"), 7, Decimal("1.0"), Decimal("1.0")),
    # eight devices - requested=7.1~8.0
    DefragAllocationExpectation(Decimal("7.1"), 8, Decimal("0.8875"), Decimal("0.8")),
    DefragAllocationExpectation(Decimal("7.2"), 8, Decimal("0.9"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("7.3"), 8, Decimal("0.9125"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("7.4"), 8, Decimal("0.925"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("7.5"), 8, Decimal("0.9375"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("7.6"), 8, Decimal("0.95"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("7.7"), 8, Decimal("0.9625"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("7.8"), 8, Decimal("0.975"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("7.9"), 8, Decimal("0.9875"), Decimal("0.9")),
    DefragAllocationExpectation(Decimal("8.0"), 8, Decimal("1.0"), Decimal("1.0")),
]


class TestDefragDensityCalculation:
    """Verify density calculations against the BA-3308 table (capacity=1.0, quantum=0.1)."""

    @pytest.fixture
    def device_capacity(self) -> Decimal:
        return Decimal("1.0")

    @pytest.fixture
    def quantum(self) -> Decimal:
        return Decimal("0.1")

    @pytest.mark.parametrize(
        "case",
        DEFRAG_ALLOCATION_CASES,
        ids=[f"requested={c.requested_resource}" for c in DEFRAG_ALLOCATION_CASES],
    )
    async def test_quantum_density_calculation(
        self,
        device_capacity: Decimal,
        quantum: Decimal,
        case: DefragAllocationExpectation,
    ) -> None:
        num_devices_needed = math.ceil(case.requested_resource / device_capacity)
        assert num_devices_needed == case.expected_num_devices

        per_device_density = case.requested_resource / Decimal(num_devices_needed)
        assert per_device_density == case.expected_density

        quantized_density = round_down(per_device_density, quantum)
        assert quantized_density == case.expected_quantized_density


class TestDefragAllocationStrategy:
    """Verify FILL/EVENLY allocation strategies with 8 GPUs (capacity=1.0, quantum=0.1)."""

    @pytest.fixture
    def defrag_map_8_fill(self) -> FractionAllocMap:
        """8 GPUs, capacity=1.0 each (total=8.0), FILL strategy, quantum=0.1."""
        return FractionAllocMap(
            device_slots={
                DeviceId(f"gpu{i}"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=Decimal("1.0"),
                )
                for i in range(8)
            },
            allocation_strategy=AllocationStrategy.FILL,
            quantum_size=Decimal("0.1"),
        )

    @pytest.fixture
    def defrag_map_8_evenly(self) -> FractionAllocMap:
        """8 GPUs, capacity=1.0 each (total=8.0), EVENLY strategy, quantum=0.1."""
        return FractionAllocMap(
            device_slots={
                DeviceId(f"gpu{i}"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=Decimal("1.0"),
                )
                for i in range(8)
            },
            allocation_strategy=AllocationStrategy.EVENLY,
            quantum_size=Decimal("0.1"),
        )

    @pytest.fixture
    def quantum(self) -> Decimal:
        return Decimal("0.1")

    @pytest.mark.parametrize(
        "case",
        DEFRAG_ALLOCATION_CASES,
        ids=[f"requested={c.requested_resource}" for c in DEFRAG_ALLOCATION_CASES],
    )
    async def test_fill_uses_expected_devices(
        self,
        defrag_map_8_fill: FractionAllocMap,
        quantum: Decimal,
        case: DefragAllocationExpectation,
    ) -> None:
        result = defrag_map_8_fill.allocate(
            {SlotName("cuda.shares"): case.requested_resource},
            allow_resource_fragmentation=False,
        )

        for dev_id, alloc_amount in result[SlotName("cuda.shares")].items():
            if alloc_amount > 0:
                # Each allocated amount should be a multiple of the quantum.
                assert alloc_amount % quantum == 0

        # Count devices that received non-zero allocation
        used_devices = sum(1 for alloc in result[SlotName("cuda.shares")].values() if alloc > 0)
        assert used_devices == case.expected_num_devices

    @pytest.mark.parametrize(
        "case",
        DEFRAG_ALLOCATION_CASES,
        ids=[f"requested={c.requested_resource}" for c in DEFRAG_ALLOCATION_CASES],
    )
    async def test_evenly_uses_at_least_expected_devices(
        self,
        defrag_map_8_evenly: FractionAllocMap,
        quantum: Decimal,
        case: DefragAllocationExpectation,
    ) -> None:
        result = defrag_map_8_evenly.allocate(
            {SlotName("cuda.shares"): case.requested_resource},
            allow_resource_fragmentation=False,
        )

        for dev_id, alloc_amount in result[SlotName("cuda.shares")].items():
            if alloc_amount > 0:
                # Each allocated amount should be a multiple of the quantum.
                assert alloc_amount % quantum == 0

        # EVENLY strategy may spread across more devices than the minimum needed,
        # because quantum rounding reduces per-device density and the shortfall spills onto additional devices.
        # Count devices that received non-zero allocation
        used_devices = sum(1 for alloc in result[SlotName("cuda.shares")].values() if alloc > 0)
        assert used_devices >= case.expected_num_devices

    @pytest.mark.parametrize(
        "requested",
        [Decimal("0.1"), Decimal("0.5"), Decimal("1.0")],
        ids=["requested=0.1", "requested=0.5", "requested=1.0"],
    )
    async def test_single_device_regression(
        self, defrag_map_8_fill: FractionAllocMap, requested: Decimal
    ) -> None:
        """requested <= 1.0 to 8 device with 1.0 capacity should use exactly 1 device."""
        result = defrag_map_8_fill.allocate(
            {SlotName("cuda.shares"): requested},
            allow_resource_fragmentation=False,
        )
        # Count devices that received non-zero allocation
        used = sum(1 for v in result[SlotName("cuda.shares")].values() if v > 0)
        assert used == 1

    async def test_fragmentation_allowed_bypasses_guard(
        self, defrag_map_8_fill: FractionAllocMap
    ) -> None:
        """allow_resource_fragmentation=True bypasses the guard.
        8 devices with 1.0 capacity can fulfill any request up to 8.0."""
        result = defrag_map_8_fill.allocate(
            {SlotName("cuda.shares"): Decimal("2.5")},
            allow_resource_fragmentation=True,
        )
        total = sum(result[SlotName("cuda.shares")].values())
        assert total == Decimal("2.5")


class TestDefragWithOccupiedDevices:
    """Verify anti-fragmentation allocation when some devices are already occupied.

    Each scenario is expressed as a list of per-device *remaining* capacity
    (index → device, value → free fraction) and a separate *requested* amount.
    ``Decimal("1.0")`` means the device is fully free.
    """

    @staticmethod
    def _make_map_with_remaining(
        device_remaining: list[Decimal],
        strategy: AllocationStrategy = AllocationStrategy.FILL,
    ) -> FractionAllocMap:
        """Create a map where each device has the given remaining capacity.

        Each device has a total capacity of ``1.0``.  The occupied portion
        (``1.0 - remaining``) is pre-allocated sequentially.
        """
        device_capacity = Decimal("1.0")
        # Pre-occupation always uses FILL so that each amount lands on
        # the next device in order, producing a deterministic layout.
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId(f"gpu{i}"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=device_capacity,
                )
                for i in range(len(device_remaining))
            },
            allocation_strategy=AllocationStrategy.FILL,
            quantum_size=Decimal("0.1"),
        )
        for remaining in device_remaining:
            occupied = device_capacity - remaining
            if occupied > 0:
                alloc_map.allocate(
                    {SlotName("cuda.shares"): occupied},
                    allow_resource_fragmentation=True,
                )
        # Switch to the target strategy for the actual test allocation.
        alloc_map.allocation_strategy = strategy
        return alloc_map

    @pytest.mark.parametrize(
        "device_remaining, requested",
        [
            # 4 GPUs: gpu0 half-free, rest free → 2 GPUs × 0.7
            ([Decimal("0.5"), Decimal("1.0"), Decimal("1.0"), Decimal("1.0")], Decimal("1.4")),
            # 4 GPUs: gpu0, gpu1 mostly free → 2 GPUs × 1.0
            ([Decimal("0.7"), Decimal("0.7"), Decimal("1.0"), Decimal("1.0")], Decimal("2.0")),
            # 2 GPUs: both above threshold → 2 GPUs × 0.7
            ([Decimal("0.9"), Decimal("1.0")], Decimal("1.4")),
        ],
    )
    async def test_fill_succeeds(
        self,
        device_remaining: list[Decimal],
        requested: Decimal,
    ) -> None:
        alloc_map = self._make_map_with_remaining(device_remaining, AllocationStrategy.FILL)
        alloc_map.allocate(
            {SlotName("cuda.shares"): requested},
            allow_resource_fragmentation=False,
        )

    @pytest.mark.parametrize(
        "device_remaining, requested",
        [
            # 4 GPUs: 2 half-free → 4 GPUs × 0.7, but gpu0,1 only 0.5
            ([Decimal("0.5"), Decimal("0.5"), Decimal("1.0"), Decimal("1.0")], Decimal("2.8")),
            # 4 GPUs: all 0.8 free → 4 GPUs × 0.9 needed, but only 0.8 available
            ([Decimal("0.8"), Decimal("0.8"), Decimal("0.8"), Decimal("0.8")], Decimal("3.6")),
            # 2 GPUs: gpu0=0.2 free → 2 GPUs × 0.8, but gpu0 below threshold
            ([Decimal("0.2"), Decimal("1.0")], Decimal("1.6")),
        ],
    )
    async def test_fill_raises(
        self,
        device_remaining: list[Decimal],
        requested: Decimal,
    ) -> None:
        alloc_map = self._make_map_with_remaining(device_remaining, AllocationStrategy.FILL)
        with pytest.raises(FractionalResourceFragmented):
            alloc_map.allocate(
                {SlotName("cuda.shares"): requested},
                allow_resource_fragmentation=False,
            )

    @pytest.mark.parametrize(
        "device_remaining, requested",
        [
            # 2 GPUs: both can hold D=0.7 share
            ([Decimal("0.7"), Decimal("0.8")], Decimal("1.4")),
        ],
    )
    async def test_fill_succeeds_with_non_uniform_free(
        self,
        device_remaining: list[Decimal],
        requested: Decimal,
    ) -> None:
        """Fill strategy succeeds when each device can hold its per-device share D."""
        alloc_map = self._make_map_with_remaining(device_remaining, AllocationStrategy.FILL)
        alloc_map.allocate(
            {SlotName("cuda.shares"): requested},
            allow_resource_fragmentation=False,
        )

    @pytest.mark.parametrize(
        "device_remaining, requested",
        [
            # 4 GPUs: gpu0 half-free, rest free → 2 GPUs × 0.7
            ([Decimal("0.5"), Decimal("1.0"), Decimal("1.0"), Decimal("1.0")], Decimal("1.4")),
            # 4 GPUs: gpu0, gpu1 mostly free → 2 GPUs × 1.0
            ([Decimal("0.7"), Decimal("0.7"), Decimal("1.0"), Decimal("1.0")], Decimal("2.0")),
            # 2 GPUs: both above threshold → 2 GPUs × 0.7
            ([Decimal("0.9"), Decimal("1.0")], Decimal("1.4")),
        ],
    )
    async def test_evenly_succeeds(
        self,
        device_remaining: list[Decimal],
        requested: Decimal,
    ) -> None:
        alloc_map = self._make_map_with_remaining(device_remaining, AllocationStrategy.EVENLY)
        alloc_map.allocate(
            {SlotName("cuda.shares"): requested},
            allow_resource_fragmentation=False,
        )

    @pytest.mark.parametrize(
        "device_remaining, requested",
        [
            # 4 GPUs: 2 half-free → 4 GPUs × 0.7, but gpu0,1 only 0.5
            ([Decimal("0.5"), Decimal("0.5"), Decimal("1.0"), Decimal("1.0")], Decimal("2.8")),
            # 4 GPUs: all 0.8 free → 4 GPUs × 0.9 needed, but only 0.8 available
            ([Decimal("0.8"), Decimal("0.8"), Decimal("0.8"), Decimal("0.8")], Decimal("3.6")),
            # 2 GPUs: gpu0=0.2 free → 2 GPUs × 0.8, but gpu0 below threshold
            ([Decimal("0.2"), Decimal("1.0")], Decimal("1.6")),
        ],
    )
    async def test_evenly_raises(
        self,
        device_remaining: list[Decimal],
        requested: Decimal,
    ) -> None:
        alloc_map = self._make_map_with_remaining(device_remaining, AllocationStrategy.EVENLY)
        with pytest.raises(FractionalResourceFragmented):
            alloc_map.allocate(
                {SlotName("cuda.shares"): requested},
                allow_resource_fragmentation=False,
            )


class TestDefragEdgeCases:
    """Edge cases for the anti-fragmentation guard, verified for both strategies."""

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_zero_request_is_pruned(self, strategy: AllocationStrategy) -> None:
        """Zero request is pruned before reaching the guard."""
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId("gpu0"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=Decimal("1.0"),
                ),
            },
            allocation_strategy=strategy,
            quantum_size=Decimal("0.1"),
        )

        result = alloc_map.allocate(
            {SlotName("cuda.shares"): Decimal("0")},
            allow_resource_fragmentation=False,
        )
        assert SlotName("cuda.shares") not in result

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_insufficient_total_devices(self, strategy: AllocationStrategy) -> None:
        """Raises FractionalResourceFragmented when total devices are insufficient."""
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId(f"gpu{i}"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=Decimal("1.0"),
                )
                for i in range(2)
            },
            allocation_strategy=strategy,
            quantum_size=Decimal("0.1"),
        )

        with pytest.raises(FractionalResourceFragmented):
            alloc_map.allocate(
                {SlotName("cuda.shares"): Decimal("3.0")},
                allow_resource_fragmentation=False,
            )

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_exact_capacity_boundary(self, strategy: AllocationStrategy) -> None:
        """Request exactly matching device capacity (boundary value)."""
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId(f"gpu{i}"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=Decimal("1.0"),
                )
                for i in range(4)
            },
            allocation_strategy=strategy,
            quantum_size=Decimal("0.1"),
        )

        # exactly 1.0 -> 1 device
        result = alloc_map.allocate(
            {SlotName("cuda.shares"): Decimal("1.0")},
            allow_resource_fragmentation=False,
        )
        # Count devices that received non-zero allocation
        used = sum(1 for v in result[SlotName("cuda.shares")].values() if v > 0)
        assert used == 1

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_all_capacity_allocation(self, strategy: AllocationStrategy) -> None:
        """Requesting full capacity uses all devices."""
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId(f"gpu{i}"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=Decimal("1.0"),
                )
                for i in range(4)
            },
            allocation_strategy=strategy,
            quantum_size=Decimal("0.1"),
        )

        result = alloc_map.allocate(
            {SlotName("cuda.shares"): Decimal("4.0")},
            allow_resource_fragmentation=False,
        )
        total = sum(result[SlotName("cuda.shares")].values())
        assert total == Decimal("4.0")

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_single_device_map(self, strategy: AllocationStrategy) -> None:
        """Single device: allocation within capacity succeeds."""
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId("gpu0"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=Decimal("1.0"),
                ),
            },
            allocation_strategy=strategy,
            quantum_size=Decimal("0.1"),
        )

        result = alloc_map.allocate(
            {SlotName("cuda.shares"): Decimal("0.7")},
            allow_resource_fragmentation=False,
        )
        assert result[SlotName("cuda.shares")][DeviceId("gpu0")] == Decimal("0.7")

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_single_device_over_capacity_raises(self, strategy: AllocationStrategy) -> None:
        """Single device: request exceeding capacity raises."""
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId("gpu0"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=Decimal("1.0"),
                ),
            },
            allocation_strategy=strategy,
            quantum_size=Decimal("0.1"),
        )

        with pytest.raises(FractionalResourceFragmented):
            alloc_map.allocate(
                {SlotName("cuda.shares"): Decimal("1.1")},
                allow_resource_fragmentation=False,
            )


class TestDefragGuardWithNonUniformFreeCapacity:
    """Verify both strategies succeed with Algorithm 2's N-increment guard.

    When the minimum N devices can't each hold D = R/N, the guard tries N+1, N+2...
    with a smaller D until it finds enough devices.
    """

    @staticmethod
    def _make_map_with_remaining(
        device_remaining: list[Decimal],
        strategy: AllocationStrategy,
    ) -> FractionAllocMap:
        device_capacity = Decimal("1.0")
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId(f"gpu{i}"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=device_capacity,
                )
                for i in range(len(device_remaining))
            },
            allocation_strategy=AllocationStrategy.FILL,
            quantum_size=Decimal("0.1"),
        )
        for remaining in device_remaining:
            occupied = device_capacity - remaining
            if occupied > 0:
                alloc_map.allocate(
                    {SlotName("cuda.shares"): occupied},
                    allow_resource_fragmentation=True,
                )
        alloc_map.allocation_strategy = strategy
        return alloc_map

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    @pytest.mark.parametrize(
        "device_remaining, requested",
        [
            # 2 GPUs: both can hold D=0.7, shortfall 0.1 covered by gpu1(0.8)
            ([Decimal("0.7"), Decimal("0.8")], Decimal("1.5")),
            # 3 GPUs: N=2, D=0.8, gpu1(0.8) + gpu2(1.0) qualify
            ([Decimal("0.4"), Decimal("0.8"), Decimal("1.0")], Decimal("1.6")),
            # 4 GPUs: N=2 succeeds, both 1.0-free devices can hold D=0.8
            ([Decimal("0.5"), Decimal("0.5"), Decimal("1.0"), Decimal("1.0")], Decimal("1.6")),
        ],
    )
    async def test_succeeds_with_non_uniform_free(
        self,
        strategy: AllocationStrategy,
        device_remaining: list[Decimal],
        requested: Decimal,
    ) -> None:
        alloc_map = self._make_map_with_remaining(device_remaining, strategy)
        result = alloc_map.allocate(
            {SlotName("cuda.shares"): requested},
            allow_resource_fragmentation=False,
        )
        total = sum(result[SlotName("cuda.shares")].values())
        assert total == requested


class TestDefragNIncrement:
    """Verify Algorithm 2: guard increments N when min-N can't hold per-device share D."""

    @staticmethod
    def _make_map_with_remaining(
        device_remaining: list[Decimal],
        strategy: AllocationStrategy,
    ) -> FractionAllocMap:
        device_capacity = Decimal("1.0")
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId(f"gpu{i}"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=device_capacity,
                )
                for i in range(len(device_remaining))
            },
            allocation_strategy=AllocationStrategy.FILL,
            quantum_size=Decimal("0.1"),
        )
        for remaining in device_remaining:
            occupied = device_capacity - remaining
            if occupied > 0:
                alloc_map.allocate(
                    {SlotName("cuda.shares"): occupied},
                    allow_resource_fragmentation=True,
                )
        alloc_map.allocation_strategy = strategy
        return alloc_map

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_n_increment_passes(self, strategy: AllocationStrategy) -> None:
        """4 GPUs each free=0.5, R=1.5.
        N=2: D=0.7, need 2 with 0.7 free → 0 → fail
        N=3: D=0.5, shortfall=0, need 3 with 0.5 free → 4 have 0.5 → pass
        """
        alloc_map = self._make_map_with_remaining(
            [Decimal("0.5")] * 4,
            strategy,
        )
        result = alloc_map.allocate(
            {SlotName("cuda.shares"): Decimal("1.5")},
            allow_resource_fragmentation=False,
        )
        total = sum(result[SlotName("cuda.shares")].values())
        assert total == Decimal("1.5")

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_n_increment_exhausted_rejects(self, strategy: AllocationStrategy) -> None:
        """4 GPUs each free=0.2, R=1.4.
        N=2: D=0.7 → fail, N=3: D=0.4 → fail, N=4: D=0.3 → fail (0.2 < 0.3)
        """
        alloc_map = self._make_map_with_remaining(
            [Decimal("0.2")] * 4,
            strategy,
        )
        with pytest.raises(FractionalResourceFragmented):
            alloc_map.allocate(
                {SlotName("cuda.shares"): Decimal("1.4")},
                allow_resource_fragmentation=False,
            )

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_n_increment_to_higher_n(self, strategy: AllocationStrategy) -> None:
        """8 GPUs each free=0.3, R=1.8.
        N=2: D=0.9 → fail (0.3 < 0.9)
        N=3: D=0.6 → fail (0.3 < 0.6)
        ...
        N=6: D=0.3 → 8 have 0.3 → pass
        """
        alloc_map = self._make_map_with_remaining(
            [Decimal("0.3")] * 8,
            strategy,
        )
        result = alloc_map.allocate(
            {SlotName("cuda.shares"): Decimal("1.8")},
            allow_resource_fragmentation=False,
        )
        total = sum(result[SlotName("cuda.shares")].values())
        assert total == Decimal("1.8")

    @pytest.mark.parametrize("strategy", [AllocationStrategy.FILL, AllocationStrategy.EVENLY])
    async def test_single_device_request_no_increment(self, strategy: AllocationStrategy) -> None:
        """R <= capacity: N is fixed at 1, no increment allowed.
        8 GPUs each free=0.3, R=0.8 → N=1 only, 0.3 < 0.8 → reject.
        """
        alloc_map = self._make_map_with_remaining(
            [Decimal("0.3")] * 8,
            strategy,
        )
        with pytest.raises(FractionalResourceFragmented):
            alloc_map.allocate(
                {SlotName("cuda.shares"): Decimal("0.8")},
                allow_resource_fragmentation=False,
            )


class TestShortfallRemainder:
    """Verify shortfall/remainder calculation matches distribute_evenly logic."""

    @pytest.fixture
    def device_capacity(self) -> Decimal:
        return Decimal("1.0")

    @pytest.fixture
    def quantum(self) -> Decimal:
        return Decimal("0.1")

    @pytest.mark.parametrize(
        "requested, expected_quantized_density, expected_extra_device_count",
        [
            # 1.5 / 2 devices = 0.75 -> quantized to 0.7, shortfall=0.1, 1 extra device
            (Decimal("1.5"), Decimal("0.7"), 1),
            # 2.5 / 3 devices = 0.833 -> quantized to 0.8, shortfall=0.1, 1 extra device
            (Decimal("2.5"), Decimal("0.8"), 1),
            # 1.1 / 2 devices = 0.55 -> quantized to 0.5, shortfall=0.1, 1 extra device
            (Decimal("1.1"), Decimal("0.5"), 1),
            # 1.2 / 2 devices = 0.6 -> quantized to 0.6, shortfall=0, no extra device
            (Decimal("1.2"), Decimal("0.6"), 0),
        ],
        ids=["requested=1.5", "requested=2.5", "requested=1.1", "requested=1.2"],
    )
    async def test_shortfall_remainder_distribution(
        self,
        device_capacity: Decimal,
        quantum: Decimal,
        requested: Decimal,
        expected_quantized_density: Decimal,
        expected_extra_device_count: int,
    ) -> None:
        num_devices = math.ceil(requested / device_capacity)
        per_device_density = requested / Decimal(num_devices)
        quantized_density = round_down(per_device_density, quantum)
        shortfall = requested - (quantized_density * num_devices)
        extra_device_count = round(shortfall / quantum)

        assert quantized_density == expected_quantized_density
        assert extra_device_count == expected_extra_device_count

        total = quantized_density * num_devices + extra_device_count * quantum
        assert total == requested

        # Verify actual allocation also succeeds
        alloc_map = FractionAllocMap(
            device_slots={
                DeviceId(f"gpu{i}"): DeviceSlotInfo(
                    slot_type=SlotTypes.COUNT,
                    slot_name=SlotName("cuda.shares"),
                    amount=device_capacity,
                )
                for i in range(8)
            },
            allocation_strategy=AllocationStrategy.FILL,
            quantum_size=quantum,
        )
        alloc_map.allocate(
            {SlotName("cuda.shares"): requested},
            allow_resource_fragmentation=False,
        )
