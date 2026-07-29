"""Existence validation shared by the read and write paths."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.manager.models.scopes import ExistenceCheck

__all__ = ("validate_existence_checks",)


async def validate_existence_checks(
    db_sess: SASession,
    checks: Sequence[ExistenceCheck[Any]],
) -> None:
    """Raise the first failing check's error, testing every check in one query.

    Reads use this to answer 404 for a scope that does not exist rather than an empty page;
    writes use it to refuse binding a new row to an owner that is not there.

    Raises:
        The error carried by the first failing :class:`ExistenceCheck`.
    """
    if not checks:
        return

    select_clauses = [
        sa.exists().where(check.column == check.value).label(f"check_{i}")
        for i, check in enumerate(checks)
    ]
    result = await db_sess.execute(sa.select(*select_clauses))
    row = result.mappings().one()

    for i, check in enumerate(checks):
        if not row[f"check_{i}"]:
            raise check.error
