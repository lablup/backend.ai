"""Operation scopes for kernel group environ rows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = ("SessionKernelGroupEnvironTarget",)


@dataclass(frozen=True)
class SessionKernelGroupEnvironTarget(ScopeTarget):
    """The environ rows of every kernel group of one session."""

    session_id: SessionID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.session_id

    @override
    def to_condition(self) -> QueryCondition:
        session_id = self.session_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelGroupEnvironRow.kernel_group_id.in_(
                sa.select(KernelGroupRow.id).where(KernelGroupRow.session_id == session_id)
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
