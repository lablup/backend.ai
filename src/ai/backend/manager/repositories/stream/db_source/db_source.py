import uuid

import sqlalchemy as sa
from sqlalchemy.orm import joinedload, noload, selectinload

from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.kernel import SessionNotFound, TooManySessionsMatched
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class StreamDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_streaming_session(
        self,
        session_name: str,
        user_uuid: uuid.UUID,
    ) -> SessionRow:
        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(SessionRow)
                .where(
                    (SessionRow.name == session_name)
                    & (SessionRow.user_uuid == user_uuid)
                    & (SessionRow.status == SessionStatus.RUNNING)
                )
                .options(
                    noload("*"),
                    selectinload(SessionRow.kernels).options(
                        noload("*"),
                        selectinload(KernelRow.agent_row).noload("*"),
                    ),
                    joinedload(SessionRow.user),
                )
                .execution_options(populate_existing=True)
            )
            result = await db_sess.execute(query)
            sessions = result.scalars().all()
            if not sessions:
                raise SessionNotFound(f"Session (name={session_name}) does not exist.")
            if len(sessions) > 1:
                session_infos = [
                    {
                        "session_id": sess.id,
                        "session_name": sess.name,
                        "status": sess.status,
                        "created_at": sess.created_at,
                    }
                    for sess in sessions
                ]
                raise TooManySessionsMatched(extra_data={"matches": session_infos})
            return sessions[0]
