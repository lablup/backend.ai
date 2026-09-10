from typing import NewType, override
from uuid import UUID

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "IdleCheckerEntityType",
    "IdleCheckerAssignmentID",
    "IdleCheckerID",
)


class IdleCheckerEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "idle_checker"

    @override
    @classmethod
    def description(cls) -> str:
        return (
            "A rule terminating sessions by lifetime, network silence or utilization,"
            " assigned to scopes."
        )


class IdleCheckerID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return IdleCheckerEntityType()


IdleCheckerAssignmentID = NewType("IdleCheckerAssignmentID", UUID)
