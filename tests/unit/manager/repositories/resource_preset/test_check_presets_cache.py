"""Round-trip of CheckPresetsResult through its cache form."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.types import ResourceSlot, SlotQuantity
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.repositories.resource_preset.db_source.types import (
    PerResourceGroupResourceData,
    PresetAllocatabilityData,
)
from ai.backend.manager.repositories.resource_preset.types import CheckPresetsResult


class TestCheckPresetsResultCache:
    @pytest.fixture
    def presets(self) -> list[PresetAllocatabilityData]:
        return [
            PresetAllocatabilityData(
                preset=ResourcePresetData(
                    id=ResourcePresetID(uuid.uuid4()),
                    name="cpu-small",
                    resource_slots=ResourceSlot({
                        "cpu": Decimal("2"),
                        "mem": Decimal("4294967296"),
                    }),
                    shared_memory=1073741824,
                    resource_group_name="default",
                ),
                allocatable=True,
            ),
            PresetAllocatabilityData(
                preset=ResourcePresetData(
                    id=ResourcePresetID(uuid.uuid4()),
                    name="gpu-large",
                    resource_slots=ResourceSlot({
                        "cpu": Decimal("8"),
                        "mem": Decimal("34359738368"),
                        "cuda.shares": Decimal("2.5"),
                    }),
                    shared_memory=None,
                    resource_group_name=None,
                ),
                allocatable=False,
            ),
        ]

    @pytest.fixture
    def result(self, presets: list[PresetAllocatabilityData]) -> CheckPresetsResult:
        return CheckPresetsResult(
            presets=presets,
            keypair_limits=[SlotQuantity("cpu", Decimal("16")), SlotQuantity("mem", Decimal("64"))],
            keypair_using=[SlotQuantity("cpu", Decimal("4")), SlotQuantity("mem", Decimal("8"))],
            keypair_remaining=[
                SlotQuantity("cpu", Decimal("12")),
                SlotQuantity("mem", Decimal("56")),
            ],
            group_limits=[SlotQuantity("cpu", Decimal("32"))],
            group_using=[SlotQuantity("cpu", Decimal("10"))],
            group_remaining=[SlotQuantity("cpu", Decimal("22"))],
            resource_group_remaining=[SlotQuantity("cpu", Decimal("100"))],
            resource_groups={
                "default": PerResourceGroupResourceData(
                    using=[SlotQuantity("cpu", Decimal("10"))],
                    remaining=[SlotQuantity("cpu", Decimal("100"))],
                ),
            },
        )

    def test_from_cache_restores_to_cache(self, result: CheckPresetsResult) -> None:
        restored = CheckPresetsResult.from_cache(result.to_cache())

        assert restored == result
