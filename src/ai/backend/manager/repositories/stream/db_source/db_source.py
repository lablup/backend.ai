import sqlalchemy as sa
from sqlalchemy.orm import noload, selectinload

from ai.backend.common.types import SessionId
from ai.backend.manager.data.kernel.types import KernelInfo
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import DEFAULT_ROLE
from ai.backend.manager.errors.kernel import (
    MainKernelNotFound,
    SessionNotFound,
    TooManyKernelsFound,
)
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.session.row import SessionRow
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
                )
                .execution_options(populate_existing=True)
            )
            session = (await db_sess.execute(query)).scalars().one_or_none()
            if session is None:
                raise SessionNotFound(f"Running session {session_id} does not exist.")
            return session

    async def get_streaming_main_kernel(self, session_id: SessionId) -> KernelInfo:
        async with self._db.begin_readonly_session() as db_sess:
            running = await db_sess.scalar(
                sa.select(SessionRow.id).where(
                    (SessionRow.id == session_id) & (SessionRow.status == SessionStatus.RUNNING)
                )
            )
            if running is None:
                raise SessionNotFound(f"Running session {session_id} does not exist.")
            main_kernels = list(
                await db_sess.scalars(
                    sa.select(KernelRow).where(
                        (KernelRow.session_id == session_id)
                        & (KernelRow.cluster_role == DEFAULT_ROLE)
                    )
                )
            )
            if len(main_kernels) > 1:
                raise TooManyKernelsFound(
                    f"Session (id: {session_id}) has more than 1 main kernel."
                )
            if not main_kernels:
                raise MainKernelNotFound(f"Session (id: {session_id}) has no main kernel.")
            return main_kernels[0].to_kernel_info()
