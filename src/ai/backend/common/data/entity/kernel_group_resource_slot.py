from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = (
    "KernelGroupResourceSlotFieldType",
    "KernelGroupResourceSlotID",
)


class KernelGroupResourceSlotFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "kernel_group_resource_slot"

    @override
    @classmethod
    def description(cls) -> str:
        return "One slot's amount a kernel group requests."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class KernelGroupResourceSlotID(FieldIdentifier):
    """One slot's amount a kernel group requests."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KernelGroupResourceSlotFieldType()
