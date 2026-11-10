"""Insert specs for the kernel_group_environ table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.manager.data.kernel_group.types import KernelGroupEnvironData
from ai.backend.manager.errors.kernel import InvalidKernelConfig
from ai.backend.manager.errors.repository import CheckConstraintViolationError
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.specs.creator import NestedFieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = ("KernelGroupEnvironCreator",)


@dataclass(frozen=True)
class KernelGroupEnvironCreator(
    NestedFieldCreator[KernelGroupID, KernelGroupEnvironRow, KernelGroupEnvironData]
):
    """Record one environment variable of a kernel group."""

    key: str
    value: str

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=CheckConstraintViolationError,
                error=InvalidKernelConfig("An environ key is not an environment variable name."),
                constraint_name="ck_kernel_group_environ_key_is_environ_name",
            ),
        )

    @override
    def build_row(self, owner_id: KernelGroupID) -> KernelGroupEnvironRow:
        return KernelGroupEnvironRow(kernel_group_id=owner_id, key=self.key, value=self.value)

    @override
    def to_data(self, row: KernelGroupEnvironRow) -> KernelGroupEnvironData:
        return row.to_data()
