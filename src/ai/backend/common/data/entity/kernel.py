"""Id of the kernels table.

A kernel runs under a session and carries no membership of its own, so its id is a
field identifier: what a kernel belongs to is knowable only through that session.
"""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("KernelID",)


KERNEL_FIELD_TYPE = FieldType("kernel")


class KernelID(FieldIdentifier):
    """A kernel row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KERNEL_FIELD_TYPE
