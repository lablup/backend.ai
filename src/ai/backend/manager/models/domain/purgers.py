"""Purge specs for the domains table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import KernelId
from ai.backend.manager.data.domain.types import DomainData
from ai.backend.manager.errors.resource import (
    DomainHasActiveKernels,
    DomainHasGroups,
    DomainHasUsers,
)
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel.row import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    KernelRow,
)
from ai.backend.manager.models.specs.purger import DataBatchPurger, EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck
from ai.backend.manager.models.user import UserRow


@dataclass
class DomainPurger(EntityPurger[DomainRow, DomainData]):
    """Removes a domain along with the scope it was."""

    domain_id: DomainID
    name: str

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.domain_id

    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def pk_value(self) -> str:
        return self.name

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return (
            ConflictCheck(
                condition=lambda: UserRow.domain_name == self.name,
                error=DomainHasUsers("There are users bound to the domain. Remove users first."),
            ),
            ConflictCheck(
                condition=lambda: GroupRow.domain_name == self.name,
                error=DomainHasGroups("There are groups bound to the domain. Remove groups first."),
            ),
        )

    @override
    def to_data(self, row: DomainRow) -> DomainData:
        return row.to_data()


@dataclass
class DomainKernelPurger(DataBatchPurger[KernelRow, KernelId]):
    """Clears the kernel rows a domain leaves behind, before the domain itself goes.

    Kernels stand outside the RBAC graph, so nothing is torn down with them.
    """

    name: str

    @override
    def build_subquery(self) -> sa.sql.Select[Any]:
        return sa.select(KernelRow).where(KernelRow.domain_name == self.name)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return (
            ConflictCheck(
                condition=lambda: (KernelRow.domain_name == self.name)
                & (KernelRow.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                error=DomainHasActiveKernels(
                    "Domain has some active kernels. Terminate them first."
                ),
            ),
        )

    @override
    def to_data(self, row: KernelRow) -> KernelId:
        return row.id
