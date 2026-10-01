"""Session dependency graph resolution helpers.

Provides recursive traversal of session dependency chains
using the ``SessionDependencyRow`` association table.
"""

from __future__ import annotations

from typing import Any

import aiotools
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import SessionId
from ai.backend.manager.errors.kernel import InvalidSessionData, SessionNotFound
from ai.backend.manager.models.kernel.row import kernels
from ai.backend.manager.models.session.row import SessionDependencyRow, SessionRow


@aiotools.lru_cache(maxsize=100)
async def _find_dependency_sessions(
    root_session_id: SessionId,
    db_session: SASession,
) -> dict[str, list[Any] | str]:
    session = (
        await db_session.execute(
            sa.select(SessionRow.id, SessionRow.name).where(SessionRow.id == root_session_id)
        )
    ).first()
    if session is None:
        raise SessionNotFound(f"Session (id={root_session_id}) does not exist.")

    session_id = str(session.id)
    session_name = session.name

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
            await _find_dependency_sessions(SessionId(dependency_session_id), db_session)
            for dependency_session_id in dependency_session_ids
        ],
    }

    return session_info


async def find_dependency_sessions(
    root_session_id: SessionId,
    db_session: SASession,
) -> dict[str, list[Any] | str]:
    return await _find_dependency_sessions(root_session_id, db_session)
