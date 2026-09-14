"""Field type and id of the kernel usage records table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("KERNEL_USAGE_RECORD_FIELD_TYPE", "KernelUsageRecordID")

KERNEL_USAGE_RECORD_FIELD_TYPE = FieldType("kernel_usage_record")


class KernelUsageRecordID(FieldIdentifier):
    """One period slice of a kernel's resource usage."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KERNEL_USAGE_RECORD_FIELD_TYPE
