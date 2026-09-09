from typing import override

from ai.backend.common.data.entity.types import EntityType

__all__ = ("AuthEntityType",)


class AuthEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "auth"

    @override
    @classmethod
    def description(cls) -> str:
        return "The authentication operations, which name no row."
