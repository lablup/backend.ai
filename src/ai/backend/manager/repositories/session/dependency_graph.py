"""Session dependency graph resolution helpers.

Provides recursive traversal of session dependency chains
using the ``SessionDependencyRow`` association table.
"""

from __future__ import annotations

from typing import Any, cast
from uuid import UUID

import aiotools
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import AccessKey
from ai.backend.manager.errors.kernel import InvalidSessionData, SessionNotFound
from ai.backend.manager.models.kernel import kernels
from ai.backend.manager.models.session import SessionDependencyRow, SessionRow


@aiotools.lru_cache(maxsize=100)
async def _find_dependency_sessions(
    session_name_or_id: UUID | str,
    db_session: SASession,
    access_key: AccessKey,
) -> dict[str, list[Any] | str]:
    sessions = await SessionRow.match_sessions(
        db_session,
        session_name_or_id,
        access_key=access_key,
    )

    if len(sessions) < 1:
        raise SessionNotFound("session not found!")

    session_id = str(sessions[0].id)
    session_name = sessions[0].name

    if not isinstance(session_name, str):
        raise InvalidSessionData("Invalid session_name type")

    kernel_query = (
        sa.select(
            kernels.c.status,
            kernels.c.status_changed,
        )
        .select_from(kernels)
        .where(kernels.c.session_id == session_id)
    )

    dependency_result = await db_session.execute(
        sa.select(SessionDependencyRow.depends_on).where(
            SessionDependencyRow.session_id == session_id
        )
    )
    dependency_session_ids = [row[0] for row in dependency_result.fetchall()]

    kernel_query_result = (await db_session.execute(kernel_query)).first()
    if kernel_query_result is None:
        raise ValueError(f"Kernel not found for session {session_id}")

    session_info: dict[str, list[Any] | str] = {
        "session_id": session_id,
        "session_name": session_name,
        "status": str(kernel_query_result[0]),
        "status_changed": str(kernel_query_result[1]),
        "depends_on": [
            await _find_dependency_sessions(dependency_session_id, db_session, access_key)
            for dependency_session_id in dependency_session_ids
        ],
    }

    return session_info


async def find_dependency_sessions(
    session_name_or_id: UUID | str,
    db_session: SASession,
    access_key: AccessKey,
) -> dict[str, list[Any] | str]:
    return await _find_dependency_sessions(session_name_or_id, db_session, access_key)


async def find_dependent_sessions(
    root_session_name_or_id: str | UUID,
    db_session: SASession,
    access_key: AccessKey,
    *,
    allow_stale: bool = False,
) -> set[UUID]:
    async def _find_dependent_sessions(session_id: UUID) -> set[UUID]:
        result = await db_session.execute(
            sa.select(SessionDependencyRow).where(SessionDependencyRow.depends_on == session_id)
        )
        dependent_sessions: set[UUID] = {x.session_id for x in result.scalars()}

        recursive_dependent_sessions: list[set[UUID]] = [
            await _find_dependent_sessions(dependent_session)
            for dependent_session in dependent_sessions
        ]

        for recursive_dependent_session in recursive_dependent_sessions:
            dependent_sessions |= recursive_dependent_session

        return dependent_sessions

    root_session = await SessionRow.get_session(
        db_session,
        root_session_name_or_id,
        access_key=access_key,
        allow_stale=allow_stale,
    )
    return await _find_dependent_sessions(cast(UUID, root_session.id))
