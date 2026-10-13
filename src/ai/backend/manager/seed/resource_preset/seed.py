from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import override

from pydantic import Field, field_validator

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.types import BinarySize, IntrinsicSlotNames, ResourceSlot
from ai.backend.manager.models.resource_preset.upserters import ResourcePresetUpserter
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class ResourcePresetSeed(SeedItem):
    """One ``resource_presets`` row, bound to the resource group its id names or to none.
    ``shared_memory`` is a binary size such as ``64m``."""

    id: ResourcePresetID
    name: str = Field(min_length=1, max_length=256)
    resource_slots: dict[str, Decimal]
    shared_memory: str | None = None
    resource_group_id: ResourceGroupID | None = None

    @field_validator("shared_memory")
    @classmethod
    def _shared_memory_in_bytes(cls, value: str | None) -> str | None:
        """A finite byte count the ``BIGINT`` column holds."""
        if value is None:
            return None
        if not 0 <= BinarySize.finite_from_str(value) <= 2**63 - 1:
            raise ValueError(f"not a byte count the column holds: {value}")
        return value

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=ResourcePresetUpserter(
                id=self.id,
                name=self.name,
                resource_slots=ResourceSlot(self.resource_slots),
                shared_memory=(
                    int(BinarySize.finite_from_str(self.shared_memory))
                    if self.shared_memory is not None
                    else None
                ),
                resource_group_id=self.resource_group_id,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    def check(self) -> list[str]:
        """The rule the create API applies to the slots: the intrinsic ones are stated."""
        intrinsic = [str(name.value) for name in IntrinsicSlotNames]
        missing = [name for name in intrinsic if name not in self.resource_slots]
        if missing:
            return [f"resource_slots leaves out {', '.join(missing)}"]
        return []

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[ResourcePresetSeed]]) -> list[SeedRejection]:
        return []
