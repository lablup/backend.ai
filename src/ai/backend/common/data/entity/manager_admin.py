from typing import override

from ai.backend.common.data.entity.types import EntityType

__all__ = ("ManagerAdminEntityType",)


class ManagerAdminEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "manager_admin"

    @override
    @classmethod
    def description(cls) -> str:
        return "The manager administration operations, which name no row."
