from __future__ import annotations

import enum
from typing import Callable, Container, Optional, Sequence, Tuple, Union, TYPE_CHECKING
from uuid import UUID
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import (
    relationship,
    selectinload,
)

from ai.backend.common.types import (
    AccessKey,
    BinarySize,
    ClusterMode,
    KernelId,
    RedisConnectionInfo,
    SessionId,
    SessionTypes,
    SessionResult,
    VFolderMount,
)

from .base import (
    EnumType, GUID, ForeignKeyIDColumn, SessionIDColumn, KernelIDColumnType,
    IDColumn, ResourceSlotColumn, URLColumn, StructuredJSONObjectListColumn,
    KVPair, ResourceLimit, KVPairInput, ResourceLimitInput,
    Base, StructuredJSONColumn, set_if_set,
)

if TYPE_CHECKING:
    from ..scheduler.types import PendingSession

__all__ = (
    'SessionStatus',
    'SessionRow',
    'SessionDependencyRow',
)


class SessionStatus(enum.Enum):
    # values are only meaningful inside the manager
    PENDING = 0
    # ---
    SCHEDULED = 5
    PREPARING = 10
    # ---
    BUILDING = 20
    PULLING = 21
    # ---
    RUNNING = 30
    RESTARTING = 31
    RESIZING = 32
    SUSPENDED = 33
    # ---
    TERMINATING = 40
    TERMINATED = 41
    ERROR = 42
    CANCELLED = 43


DEAD_SESSION_STATUSES = (
    SessionStatus.CANCELLED,
    SessionStatus.TERMINATED,
)


async def _match_sessions(
    db_session: SASession,
    build_query: Callable,
    session_name_or_id: Union[str, UUID],
    allow_prefix: bool=False,
) -> Sequence[SessionRow]:
    id_cond = (sa.sql.expression.cast(SessionRow.id, sa.String).like(f'{session_name_or_id}%'))
    name_cond = (SessionRow.name == (f'{session_name_or_id}'))
    id_query = build_query(id_cond)
    name_query = build_query(name_cond)

    match_queries = [id_query, name_query]
    if allow_prefix:
        prefix_name_cond = (SessionRow.name.like(f'{session_name_or_id}%'))
        prefix_name_query = build_query(prefix_name_cond)
        match_queries.append(prefix_name_query)

    for query in match_queries:
        result = await db_session.execute(query)
        rows = result.scalars().all()
        if not rows:
            continue
        return rows
    return []

class SessionRow(Base):
    __tablename__ = 'sessions'
    id = SessionIDColumn()
    creation_id = sa.Column('creation_id', sa.String(length=32), unique=False, index=False)
    name = sa.Column('name', sa.String(length=64), unique=False, index=True)
    session_type = sa.Column('session_type', EnumType(SessionTypes), index=True, nullable=False,  # previously sess_type
              default=SessionTypes.INTERACTIVE, server_default=SessionTypes.INTERACTIVE.name)

    cluster_mode = sa.Column('cluster_mode', sa.String(length=16), nullable=False,
              default=ClusterMode.SINGLE_NODE, server_default=ClusterMode.SINGLE_NODE.name)
    cluster_size = sa.Column('cluster_size', sa.Integer, nullable=False, default=1)
    kernels = relationship('KernelRow', back_populates='session', primaryjoin='SessionRow.id==KernelRow.session_id')
    main_kernel_id = sa.Column('main_kernel_id', KernelIDColumnType, sa.ForeignKey('kernels.id'),
                  nullable=False, unique=True, index=True)
    main_kernel = relationship('KernelRow', foreign_keys=[main_kernel_id])

    # Resource ownership
    scaling_group_name = sa.Column('scaling_group_name', sa.ForeignKey('scaling_groups.name'), index=True, nullable=True)
    scaling_group = relationship('ScalingGroupRow', back_populates='sessions')
    domain_name = sa.Column('domain_name', sa.String(length=64), sa.ForeignKey('domains.name'), nullable=False)
    domain = relationship('DomainRow', back_populates='sessions')
    group_id = ForeignKeyIDColumn('group_id', 'groups.id', nullable=False)
    group = relationship('GroupRow', back_populates='sessions')
    user_uuid = ForeignKeyIDColumn('user_uuid', 'users.uuid', nullable=False)
    user = relationship('UserRow', back_populates='sessions')
    kp_access_key = sa.Column('kp_access_key', sa.String(length=20), sa.ForeignKey('keypairs.access_key'))
    access_key = relationship('KeyPairRow', back_populates='sessions')

    # if image_id is null, should find a image field from related kernel row.
    image_id = ForeignKeyIDColumn('image_id', 'images.id')
    image = relationship('ImageRow', back_populates='sessions')
    tag = sa.Column('tag', sa.String(length=64), nullable=True)

    # Resource occupation
    # occupied_slots = sa.Column('occupied_slots', ResourceSlotColumn(), nullable=False)
    occupying_slots = sa.Column('occupying_slots', ResourceSlotColumn(), nullable=False)
    requested_slots = sa.Column('requested_slots', ResourceSlotColumn(), nullable=False)
    vfolder_mounts = sa.Column('vfolder_mounts', StructuredJSONObjectListColumn(VFolderMount), nullable=True)
    resource_opts = sa.Column('resource_opts', pgsql.JSONB(), nullable=True, default={})
    bootstrap_script= sa.Column('bootstrap_script', sa.String(length=16 * 1024), nullable=True)

    # Lifecycle
    created_at = sa.Column('created_at', sa.DateTime(timezone=True),
              server_default=sa.func.now(), index=True)
    terminated_at = sa.Column('terminated_at', sa.DateTime(timezone=True),
              nullable=True, default=sa.null(), index=True)
    starts_at = sa.Column('starts_at', sa.DateTime(timezone=True),
              nullable=True, default=sa.null())
    status = sa.Column('status', EnumType(SessionStatus),
              default=SessionStatus.PENDING,
              server_default=SessionStatus.PENDING.name,
              nullable=False, index=True)
    status_changed = sa.Column('status_changed', sa.DateTime(timezone=True), nullable=True, index=True)
    status_info = sa.Column('status_info', sa.Unicode(), nullable=True, default=sa.null())
    status_data = sa.Column('status_data', pgsql.JSONB(), nullable=True, default=sa.null())
    callback_url = sa.Column('callback_url', URLColumn, nullable=True, default=sa.null())

    startup_command = sa.Column('startup_command', sa.Text, nullable=True)
    result = sa.Column('result', EnumType(SessionResult),
              default=SessionResult.UNDEFINED,
              server_default=SessionResult.UNDEFINED.name,
              nullable=False, index=True)

    # Resource metrics measured upon termination
    num_queries = sa.Column('num_queries', sa.BigInteger(), default=0)
    last_stat = sa.Column('last_stat', pgsql.JSONB(), nullable=True, default=sa.null())

    __table_args__ = (
        # indexing
        sa.Index(
            'ix_sessions_updated_order',
            sa.func.greatest('created_at', 'terminated_at', 'status_changed'),
            unique=False,
        ),
    )

    @classmethod
    async def match_sessions_attrs(
        cls,
        db_session: SASession,
        session_name_or_id: Union[str, UUID],
        access_key: AccessKey,
        info_cols: Sequence,
        *,
        allow_prefix: bool=False,
        allow_stale: bool=True,
        max_matches: int=10,
    ) -> Sequence[SessionRow]:
        def build_query(base_cond):
            cond = base_cond & (SessionRow.kp_access_key == access_key)
            if not allow_stale:
                cond = cond & (~SessionRow.status.in_(DEAD_SESSION_STATUSES))
            query = (
                sa.select(*info_cols)
                .where(cond)
                .order_by(sa.desc(SessionRow.created_at))
                .limit(max_matches).offset(0)
            )
            return query

        return await _match_sessions(
            db_session, build_query, session_name_or_id, allow_prefix,
        )

    @classmethod
    async def match_sessions(
        cls,
        db_session: SASession,
        session_name_or_id: Union[str, UUID],
        access_key: AccessKey,
        *,
        allow_prefix: bool=False,
        allow_stale: bool=True,
        for_update: bool=False,
        max_matches: int=10,
        load_kernels: bool=False,
        load_main_kernel: bool=False,
    ) -> Sequence[SessionRow]:
        """
        Match the prefix of session ID or session name among the sessions
        that belongs to the given access key, and return the list of SessionRow.
        """

        def build_query(base_cond):
            cond = base_cond & (SessionRow.kp_access_key == access_key)
            if not allow_stale:
                cond = cond & (~SessionRow.status.in_(DEAD_SESSION_STATUSES))
            query = (
                sa.select(SessionRow)
                .where(cond)
                .order_by(sa.desc(SessionRow.created_at))
                .limit(max_matches).offset(0)
            )
            if for_update:
                query = query.with_for_update()
            if load_kernels:
                query = query.options(selectinload(SessionRow.kernels))
            if load_main_kernel:
                query = query.options(selectinload(SessionRow.main_kernel))
            return query

        return await _match_sessions(
            db_session, build_query, session_name_or_id, allow_prefix,
        )
    
    @classmethod
    async def get_sessions(
        cls,
        db_session: SASession,
        session_names: Container[str],
        access_key: AccessKey,
        info_cols: Sequence,
        *,
        allow_stale=False,
    ) -> Sequence[SessionRow]:
        default_cols = [
            SessionRow.id, SessionRow.name, SessionRow.access_key,
        ]
        cols = set(default_cols + info_cols)

        cond = (
            (SessionRow.name.in_(session_names)) &
            (SessionRow.kp_access_key == access_key)
        )
        if not allow_stale:
            cond = cond & (~SessionRow.status.in_(DEAD_SESSION_STATUSES))
        query = (
            sa.select(cols)
            .select_from(SessionRow)
            .where(cond)
        )
        result = await db_session.execute(query)
        return result.scalars().all()


class SessionDependencyRow(Base):
    __tablename__ = 'session_dependencies'
    session_id = sa.Column('session_id', GUID,
              sa.ForeignKey('sessions.id', onupdate='CASCADE', ondelete='CASCADE'),
              index=True, nullable=False)
    depends_on = sa.Column('depends_on', GUID,
              sa.ForeignKey('sessions.id', onupdate='CASCADE', ondelete='CASCADE'),
              index=True, nullable=False)

    __table_args__ = (
        # constraint
        sa.PrimaryKeyConstraint(
            'session_id', 'depends_on',
            name='sess_dep_pk'),
    )

    @classmethod
    async def check_all_dependencies(
        cls,
        db_session: SASession,
        sess_ctx: PendingSession,
    ) -> Tuple[bool, Optional[str]]:
        j = sa.join(
            SessionDependencyRow,
            SessionRow,
            SessionDependencyRow.depends_on == SessionDependencyRow.session_id,
        )
        query = (
            sa.select(SessionRow.id, SessionRow.name, SessionRow.result)
            .select_from(j)
            .where(SessionDependencyRow.session_id == sess_ctx.session_id)
        )
        result = await db_session.execute(query)
        rows = result.scalars().all()
        pending_dependencies = []
        sess_row: SessionRow
        for sess_row in rows:
            if sess_row.result != SessionResult.SUCCESS:
                pending_dependencies.append(sess_row)
        all_success = (not pending_dependencies)
        if all_success:
            return (True,)
        return (
            False,
            "Waiting dependency sessions to finish as success. ({})".format(
                ", ".join(f"{sess_row.name} ({sess_row.session_id})" for sess_row in pending_dependencies),
            )
        )
