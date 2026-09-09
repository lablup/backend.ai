"""Field type and id of the kernel scheduling history table."""

from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("KernelSchedulingHistoryFieldType", "KernelSchedulingHistoryID")


class KernelSchedulingHistoryFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "kernel_scheduling_history"

    @override
    @classmethod
    def description(cls) -> str:
        return "One scheduling step recorded for a kernel."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class KernelSchedulingHistoryID(FieldIdentifier):
    """A kernel scheduling history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KernelSchedulingHistoryFieldType()
