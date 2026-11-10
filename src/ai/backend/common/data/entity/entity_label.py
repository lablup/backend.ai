from typing import NewType, override

from ai.backend.common.data.entity.types import DanglingFieldType, FieldIdentifier, FieldType

__all__ = ("EntityLabelID", "EntityLabelKey")


class EntityLabelFieldType(DanglingFieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "label"

    @override
    @classmethod
    def description(cls) -> str:
        return "One key and value label put on an entity of any kind."


EntityLabelKey = NewType("EntityLabelKey", str)
"""The key half of a ``key=value`` label. Names no entity: which rows carry it is what
a query answers, not what the value declares."""


class EntityLabelID(FieldIdentifier):
    """One ``key=value`` label put on one entity."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return EntityLabelFieldType()
