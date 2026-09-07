from typing import NewType, override
from uuid import UUID

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "IDLE_CHECKER_ENTITY_TYPE",
    "IdleCheckerAssignmentID",
    "IdleCheckerID",
)


# Raw string mirroring the RBAC-managed EntityType.IDLE_CHECKER value.
IDLE_CHECKER_ENTITY_TYPE = EntityType("idle_checker")


class IdleCheckerID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return IDLE_CHECKER_ENTITY_TYPE


IdleCheckerAssignmentID = NewType("IdleCheckerAssignmentID", UUID)
