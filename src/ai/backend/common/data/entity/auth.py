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
        return "An authentication operation that names no user, such as a login."
