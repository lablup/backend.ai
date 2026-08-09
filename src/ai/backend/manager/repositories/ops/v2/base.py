"""Session-bound base of the v2 ops.

Holds the session and the read-safe scope primitives both sides share; the write
primitives live in :class:`~.write_base.V2WriteOpsBase` so the read side never
inherits write behavior.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.models.scopes import OperationScope

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession as SASession


class V2OpsBase:
    """Holds the session the ops are bound to, plus the scope-condition primitives."""

    _sess: SASession

    def __init__(self, sess: SASession) -> None:
        self._sess = sess

    def _scopes_condition(self, scopes: Sequence[OperationScope]) -> sa.ColumnElement[bool]:
        return sa.or_(*[scope.to_condition()() for scope in scopes])

    async def _validate_scope_existence(self, scopes: Sequence[OperationScope]) -> None:
        checks = [check for scope in scopes for check in scope.existence_checks]
        if not checks:
            return
        select_clauses = [
            sa.exists().where(check.column == check.value).label(f"check_{i}")
            for i, check in enumerate(checks)
        ]
        result = await self._sess.execute(sa.select(*select_clauses))
        row = result.mappings().one()
        for i, check in enumerate(checks):
            if not row[f"check_{i}"]:
                raise check.error
