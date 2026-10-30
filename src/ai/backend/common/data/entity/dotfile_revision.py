from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.types import DanglingFieldType, FieldIdentifier, FieldType

__all__ = ("DotfileRevisionFieldType", "DotfileRevisionID")


class DotfileRevisionFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "dotfile_revision"

    @override
    @classmethod
    def description(cls) -> str:
        return "One write of a dotfile's permission and content, numbered within that dotfile."


class DotfileRevisionID(FieldIdentifier):
    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DotfileRevisionFieldType()
