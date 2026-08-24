from typing import NewType, override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("LabelID", "LabelKey")

LABEL_FIELD_TYPE = FieldType("label")

LabelKey = NewType("LabelKey", str)
"""The key half of a ``key=value`` label. Names no entity: which rows carry it is what
a query answers, not what the value declares."""


class LabelID(FieldIdentifier):
    """One ``key=value`` label put on one entity."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return LABEL_FIELD_TYPE
