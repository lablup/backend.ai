from typing import override

from ai.backend.common.data.entity.types import EntityType

__all__ = ("ScopeAdminEntityType",)


class ScopeAdminEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "scope_admin"

    @override
    @classmethod
    def description(cls) -> str:
        return (
            "Administration of a scope. Which scope is administered comes from where the "
            "permission is granted, so this type has no rows of its own."
        )
