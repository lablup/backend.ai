from typing import override

from ai.backend.common.data.entity.types import DanglingFieldType

__all__ = ("SecretFieldType",)


# The stored secrets of every encrypted column. Named on its own rather than under one
# of the entities holding them: the same operation covers all of those columns.
class SecretFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "secret"

    @override
    @classmethod
    def description(cls) -> str:
        return "Stored secret values across encrypted columns of multiple entity kinds."
