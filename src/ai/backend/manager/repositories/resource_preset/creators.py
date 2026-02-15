from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.exception import ResourcePresetConflict
from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class ResourcePresetCreatorSpec(CreatorSpec[ResourcePresetRow]):
    """CreatorSpec for resource preset."""

    name: str
    resource_slots: ResourceSlot
    shared_memory: str | None
    scaling_group_name: str | None

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=ResourcePresetConflict(
                    f"Duplicate resource preset name (name:{self.name}, scaling_group:{self.scaling_group_name})"
                ),
            ),
        )

    @override
    def build_row(self) -> ResourcePresetRow:
        row = ResourcePresetRow()
        row.name = self.name
        row.resource_slots = self.resource_slots
        row.shared_memory = (
            int(BinarySize.from_str(self.shared_memory)) if self.shared_memory else None
        )
        row.scaling_group_name = self.scaling_group_name
        return row
