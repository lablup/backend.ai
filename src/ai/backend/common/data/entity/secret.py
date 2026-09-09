from typing import override

from ai.backend.common.data.entity.types import DanglingFieldType

__all__ = ("SecretFieldType",)


class SecretFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "secret"

    @override
    @classmethod
    def description(cls) -> str:
        return "One encrypted column value, on whichever row holds it."
