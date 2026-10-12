from __future__ import annotations

from collections.abc import Sequence
from typing import override

from pydantic import Field

from ai.backend.common.data.entity.resource_slot import ResourceSlotTypeUUID
from ai.backend.common.types import SlotTypes
from ai.backend.manager.models.resource_slot.types import NumberFormat
from ai.backend.manager.models.resource_slot.upserters import ResourceSlotTypeUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class ResourceSlotTypeSeed(SeedItem):
    """One ``resource_slot_types`` row, keyed by its uuid. A field left out takes the
    column default."""

    uuid: ResourceSlotTypeUUID
    slot_name: str = Field(min_length=1, max_length=64)
    slot_type: SlotTypes
    required: bool = False
    enabled: bool = True
    display_name: str = Field(default="", max_length=128)
    description: str = Field(default="", max_length=256)
    display_unit: str = Field(default="", max_length=32)
    display_icon: str = Field(default="", max_length=64)
    number_format: NumberFormat = NumberFormat()
    rank: int = Field(default=0, ge=-(2**31), le=2**31 - 1)

    @override
    def key(self) -> str:
        return str(self.uuid)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=ResourceSlotTypeUpserter(
                uuid=self.uuid,
                slot_name=self.slot_name,
                slot_type=self.slot_type,
                required=self.required,
                enabled=self.enabled,
                display_name=self.display_name,
                description=self.description,
                display_unit=self.display_unit,
                display_icon=self.display_icon,
                number_format=self.number_format,
                rank=self.rank,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ResourceSlotTypeSeed]]) -> list[SeedRejection]:
        return []
