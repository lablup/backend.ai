"""Field type and id of the kernel scheduling history table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("KERNEL_SCHEDULING_HISTORY_FIELD_TYPE", "KernelSchedulingHistoryID")

KERNEL_SCHEDULING_HISTORY_FIELD_TYPE = FieldType("kernel_scheduling_history")


class KernelSchedulingHistoryID(FieldIdentifier):
    """A kernel scheduling history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KERNEL_SCHEDULING_HISTORY_FIELD_TYPE
