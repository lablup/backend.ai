from typing import NewType, override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("EntityLabelID", "EntityLabelKey")

ENTITY_LABEL_FIELD_TYPE = FieldType("label")

EntityLabelKey = NewType("EntityLabelKey", str)
"""The key half of a ``key=value`` label. Names no entity: which rows carry it is what
a query answers, not what the value declares."""


class EntityLabelID(FieldIdentifier):
    """One ``key=value`` label put on one entity."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ENTITY_LABEL_FIELD_TYPE
