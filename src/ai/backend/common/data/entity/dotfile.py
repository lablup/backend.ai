from typing import override

from ai.backend.common.data.entity.types import DanglingFieldType, FieldIdentifier, FieldType


class DotfileFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "dotfile"

    @override
    @classmethod
    def description(cls) -> str:
        return "A packed dotfile collection set on an entity."


class DotfileID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DotfileFieldType()
