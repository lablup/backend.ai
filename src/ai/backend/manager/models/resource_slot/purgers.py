from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.resource_slot.types import ResourceSlotTypeData
from ai.backend.manager.errors.resource_slot import ResourceSlotTypeInUse
from ai.backend.manager.models.resource_slot.row import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ModelCardResourceRequirementRow,
    PresetResourceSlotRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.specs.purger import GlobalEntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ResourceSlotTypePurger(GlobalEntityPurger[ResourceSlotTypeRow, ResourceSlotTypeData]):
    """Purger for a resource slot type, keyed by its ``slot_name`` primary key.

    Every table that keeps the name as an FK is declared as a conflict check, so a
    slot type still spoken of anywhere is refused instead of failing on the
    constraint.
    """

    slot_name: str

    @override
    def row_class(self) -> type[ResourceSlotTypeRow]:
        return ResourceSlotTypeRow

    @override
    def pk_value(self) -> str:
        return self.slot_name

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        slot_name = self.slot_name
        return (
            ConflictCheck(
                condition=lambda: AgentResourceRow.slot_name == slot_name,
                error=ResourceSlotTypeInUse(
                    f"Resource slot type '{slot_name}' is still reported by an agent."
                ),
            ),
            ConflictCheck(
                condition=lambda: ResourceAllocationRow.slot_name == slot_name,
                error=ResourceSlotTypeInUse(
                    f"Resource slot type '{slot_name}' is still allocated to a kernel."
                ),
            ),
            ConflictCheck(
                condition=lambda: ModelCardResourceRequirementRow.slot_name == slot_name,
                error=ResourceSlotTypeInUse(
                    f"Resource slot type '{slot_name}' is still required by a model card."
                ),
            ),
            ConflictCheck(
                condition=lambda: PresetResourceSlotRow.slot_name == slot_name,
                error=ResourceSlotTypeInUse(
                    f"Resource slot type '{slot_name}' is still used by a deployment preset."
                ),
            ),
            ConflictCheck(
                condition=lambda: DeploymentRevisionResourceSlotRow.slot_name == slot_name,
                error=ResourceSlotTypeInUse(
                    f"Resource slot type '{slot_name}' is still used by a deployment revision."
                ),
            ),
        )

    @override
    def to_data(self, row: ResourceSlotTypeRow) -> ResourceSlotTypeData:
        return row.to_data()
