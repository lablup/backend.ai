from __future__ import annotations

from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec


@dataclass
class DomainKernelBatchPurgerSpec(BatchPurgerSpec[KernelRow]):
    """PurgerSpec for deleting all kernels belonging to a domain."""

    domain_name: str

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[KernelRow]]:
        return sa.select(KernelRow).where(KernelRow.domain_name == self.domain_name)


@dataclass
class DomainBatchPurgerSpec(BatchPurgerSpec[DomainRow]):
    """PurgerSpec for deleting a domain."""

    domain_name: str

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[DomainRow]]:
        return sa.select(DomainRow).where(DomainRow.name == self.domain_name)
