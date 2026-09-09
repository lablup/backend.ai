from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = (
    "ProjectEntityType",
    "PROJECT_SCOPE_TYPE",
    "ProjectID",
)


class ProjectEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "project"

    @override
    @classmethod
    def description(cls) -> str:
        return "A group of users inside a domain that owns sessions and vfolders."


PROJECT_SCOPE_TYPE = ScopeType(ProjectEntityType())


class ProjectID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ProjectEntityType()
