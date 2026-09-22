"""Operation scopes for kernels."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget

__all__ = ("SessionKernelTarget",)


@dataclass(frozen=True)
class SessionKernelTarget(ScopeTarget):
    """The kernels of one session."""

    session_id: SessionID

    @override
    def scope_id(self) -> EntityIdentifier:
        return self.session_id

    @override
    def to_condition(self) -> QueryCondition:
        session_id = self.session_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelRow.session_id == session_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()
