import sqlalchemy as sa
from sqlalchemy.orm import joinedload, noload, selectinload

from ai.backend.common.types import SessionId
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class StreamDBSource:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_streaming_session(self, session_id: SessionId) -> SessionRow:
        async with self._db.begin_readonly_session() as db_sess:
            query = (
                sa.select(SessionRow)
                .where((SessionRow.id == session_id) & (SessionRow.status == SessionStatus.RUNNING))
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
            session = (await db_sess.execute(query)).scalars().one_or_none()
            if session is None:
                raise SessionNotFound(f"Running session {session_id} does not exist.")
            return session
