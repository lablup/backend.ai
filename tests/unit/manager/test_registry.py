from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from ai.backend.common.types import BinarySize, DeviceId, SlotName
from ai.backend.manager.registry import AgentRegistry


@pytest.mark.asyncio
async def test_convert_resource_spec_to_resource_slot(
    registry_ctx: tuple[
        AgentRegistry, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock, MagicMock
    ],
):
    registry, _, _, _, _, _, _ = registry_ctx
    allocations = {
        "cuda": {
            SlotName("cuda.shares"): {
                DeviceId("a0"): "2.5",
                DeviceId("a1"): "2.0",
            },
        },
    }
    converted_allocations = registry.convert_resource_spec_to_resource_slot(allocations)
    assert converted_allocations["cuda.shares"] == Decimal("4.5")
    allocations = {
        "cpu": {
            SlotName("cpu"): {
                DeviceId("a0"): "3",
                DeviceId("a1"): "1",
            },
        },
        "ram": {
            SlotName("ram"): {
                DeviceId("b0"): "2.5g",
                DeviceId("b1"): "512m",
            },
        },
    }
    converted_allocations = registry.convert_resource_spec_to_resource_slot(allocations)
    assert converted_allocations["cpu"] == Decimal("4")
    assert converted_allocations["ram"] == Decimal(BinarySize.from_str("1g")) * 3
