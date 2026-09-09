from typing import override

from ai.backend.common.data.entity.types import EntityType

__all__ = ("SecretEntityType",)


# The stored secrets of every encrypted column. Named on its own rather than under one
# of the entities holding them: the same operation covers all of those columns.
class SecretEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "secret"

    @override
    @classmethod
    def description(cls) -> str:
        return "A named secret value."
