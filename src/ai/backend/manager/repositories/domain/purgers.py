from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.manager.errors.resource import DomainHasGroups, DomainHasUsers
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec, PurgerSpec
from ai.backend.manager.repositories.base.types import ConflictCheck


@dataclass
class DomainKernelBatchPurgerSpec(BatchPurgerSpec[KernelRow]):
    """PurgerSpec for deleting all kernels belonging to a domain."""

    domain_name: str

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[KernelRow]]:
        return sa.select(KernelRow).where(KernelRow.domain_name == self.domain_name)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class DomainBatchPurgerSpec(BatchPurgerSpec[DomainRow]):
    """PurgerSpec for deleting a domain."""

    domain_name: str

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[DomainRow]]:
        return sa.select(DomainRow).where(DomainRow.name == self.domain_name)

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class DomainPurgerSpec(PurgerSpec[DomainRow]):
    """PurgerSpec for purging a single domain."""

    domain_name: str

    @override
    def row_class(self) -> type[DomainRow]:
        return DomainRow

    @override
    def pk_value(self) -> str:
        return self.domain_name

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return (
            ConflictCheck(
                condition=lambda: UserRow.domain_name == self.domain_name,
                error=DomainHasUsers("There are users bound to the domain. Remove users first."),
            ),
            ConflictCheck(
                condition=lambda: GroupRow.domain_name == self.domain_name,
                error=DomainHasGroups("There are groups bound to the domain. Remove groups first."),
            ),
        )
