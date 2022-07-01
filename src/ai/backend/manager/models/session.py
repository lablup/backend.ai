from __future__ import annotations

import enum
from typing import Any, List, Mapping, Optional, Sequence, Tuple, Union
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pgsql
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import noload, relationship, selectinload

from ai.backend.common.types import (
    AccessKey,
    ClusterMode,
    KernelId,
    SessionId,
    SessionResult,
    SessionTypes,
    VFolderMount,
)

from ..api.exceptions import (
    GenericForbidden,
    MainKernelNotFound,
    UnknownDependencySession,
)
from ..defs import DEFAULT_ROLE
from .base import (
    GUID,
    Base,
    EnumType,
    ForeignKeyIDColumn,
    ResourceSlotColumn,
    SessionIDColumn,
    StructuredJSONObjectListColumn,
    URLColumn,
)
from .kernel import KernelRow, KernelStatus
from .keypair import KeyPairRow

__all__ = (
    'SessionStatus',
    'DEAD_SESSION_STATUSES',
    'AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES',
    'USER_RESOURCE_OCCUPYING_SESSION_STATUSES',
    'transit_session_lifecycle',
    'SessionRow', 'enqueue_session', 'get_sgroup_managed_sessions',
    'update_kernel', 'update_session_kernels',
    'get_sessions_by_status', 'get_schedulerable_session',
    'match_sessions',
    'get_sessions_by_id',
    'SessionDependencyRow',
    'check_all_dependencies',
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

# statuses to consider when calculating current resource usage
AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES = tuple(
    e for e in SessionStatus
    if e not in (
        SessionStatus.TERMINATED,
        SessionStatus.PENDING,
        SessionStatus.CANCELLED,
    )
)

USER_RESOURCE_OCCUPYING_SESSION_STATUSES = tuple(
    e for e in SessionStatus
    if e not in (
        SessionStatus.TERMINATING,
        SessionStatus.TERMINATED,
        SessionStatus.PENDING,
        SessionStatus.CANCELLED,
    )
)


_KERNEL_SESSION_STATUS_MAPPING = {
    KernelStatus.PENDING: SessionStatus.PENDING,
    KernelStatus.SCHEDULED: SessionStatus.SCHEDULED,
    KernelStatus.PREPARING: SessionStatus.PREPARING,
    KernelStatus.BUILDING: SessionStatus.BUILDING,
    KernelStatus.PULLING: SessionStatus.PULLING,
    KernelStatus.RUNNING: SessionStatus.RUNNING,
    KernelStatus.RESTARTING: SessionStatus.RESTARTING,
    KernelStatus.RESIZING: SessionStatus.RESIZING,
    KernelStatus.SUSPENDED: SessionStatus.SUSPENDED,
    KernelStatus.TERMINATING: SessionStatus.TERMINATING,
    KernelStatus.TERMINATED: SessionStatus.TERMINATED,
    KernelStatus.ERROR: SessionStatus.ERROR,
    KernelStatus.CANCELLED: SessionStatus.CANCELLED,
}


def _transit_destroy_session(current, forced) -> SessionStatus:
    match current:
        case SessionStatus.PENDING:
            return SessionStatus.CANCELLED
        case SessionStatus.PULLING:
            raise GenericForbidden('Cannot destroy kernels in pulling status')
        case SessionStatus.SCHEDULED | SessionStatus.PREPARING | SessionStatus.TERMINATING | SessionStatus.ERROR:
            if not forced:
                raise GenericForbidden(
                    'Cannot destroy kernels in scheduled/preparing/terminating/error status',
                )
            return SessionStatus.TERMINATED
        case _:
            return SessionStatus.TERMINATING


def transit_session_lifecycle(current, job, forced=False) -> SessionStatus:
    match job:
        case 'destroy':
            return _transit_destroy_session(current, forced)
        case _:
            raise RuntimeError('No such job is declared.')


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

    # Resource ownership
    scaling_group_name = sa.Column('scaling_group_name', sa.ForeignKey('scaling_groups.name'), index=True, nullable=True)
    scaling_group = relationship('ScalingGroupRow', back_populates='sessions')
    target_sgroup_names = sa.Column('target_sgroup_names', sa.ARRAY(sa.String(length=64)),
              default='{}', server_default='{}', nullable=True)
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
    environ = sa.Column('environ', pgsql.JSONB(), nullable=True, default={})
    bootstrap_script = sa.Column('bootstrap_script', sa.String(length=16 * 1024), nullable=True)

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
    # status_data contains a JSON object that contains detailed data for the last status change.
    # During scheduling (as PENDING + ("no-available-instances" | "predicate-checks-failed")):
    # {
    #   "scheduler": {
    #     // shceudler attempt information
    #     // NOTE: the whole field may be NULL before the first attempt!
    #     "retries": 5,
    #         // the number of scheudling attempts (used to avoid HoL blocking as well)
    #     "last_try": "2021-05-01T12:34:56.123456+09:00",
    #         // an ISO 8601 formatted timestamp of the last attempt
    #     "failed_predicates": [
    #       { "name": "concurrency", "msg": "You cannot run more than 30 concurrent sessions." },
    #           // see the manager.scheduler.predicates module for possible messages
    #       ...
    #     ],
    #     "passed_predicates": [ {"name": "reserved_time"}, ... ],  // names only
    #   }
    # }
    #
    # While running: the field is NULL.
    #
    # After termination:
    # {
    #   "kernel": {
    #     // termination info for the individual kernel
    #     "exit_code": 123,
    #         // maybe null during termination
    #   },
    #   "session": {
    #     // termination info for the session
    #     "status": "terminating" | "terminated"
    #         // "terminated" means all kernels that belong to the same session has terminated.
    #         // used to prevent duplication of SessionTerminatedEvent
    #   }
    # }
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

    @property
    def main_kernel(self) -> KernelRow:
        try:
            return tuple(kern for kern in self.kernels if kern.cluster_role == DEFAULT_ROLE)[0]
        except IndexError:
            raise MainKernelNotFound


async def match_sessions(
    db_session: SASession,
    session_name_or_id: Union[str, UUID],
    access_key: AccessKey,
    *,
    allow_prefix: bool = False,
    allow_stale: bool = True,
    for_update: bool = False,
    max_matches: int = 10,
    load_intrinsic: bool = False,
) -> List[SessionRow]:
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

        if load_intrinsic:
            query = query.options(
                noload('*'),
                selectinload(SessionRow.image).noload('*'),
                selectinload(SessionRow.kernels)
                .options(
                    noload('*'),
                    selectinload(KernelRow.image).noload('*'),
                    selectinload(KernelRow.agent).noload('*'),
                ),
            )

        return query

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


async def get_sessions_by_id(
    db_session: SASession,
    session_ids: Sequence[SessionId],
    access_key=None,
    *,
    load_intrinsic=False,
    do_ordering=False,
) -> SessionRow:
    cond = (SessionRow.id.in_(session_ids))
    if access_key is not None:
        cond = cond & (SessionRow.kp_access_key == access_key)
    query = (
        sa.select(SessionRow)
        .where(cond)
    )
    if load_intrinsic:
        query = query.options(
            noload('*'),
            selectinload(SessionRow.image),
            selectinload(SessionRow.access_key)
            .options(
                noload('*'),
                selectinload(KeyPairRow.resource_policy).noload('*'),
            ),
            selectinload(SessionRow.kernels)
            .options(
                noload('*'),
                selectinload(KernelRow.image).noload('*'),
                selectinload(KernelRow.agent).noload('*'),
            ),
        )
    if do_ordering:
        query = query.order_by(SessionRow.created_at)
    result = await db_session.execute(query)
    return result.scalars().all()


async def get_sessions_by_status(
    db_session: SASession,
    status: SessionStatus | List[SessionStatus],
    sgroup_name: str | None = None,
    load_intrinsic: bool = False,
    do_ordering: bool = False,
) -> List[SessionRow]:
    if isinstance(status, SessionStatus):
        cond = (SessionRow.status == status)
    elif len(status) == 1:
        cond = (SessionRow.status == status[0])
    else:
        cond = (SessionRow.status.in_(status))
    if sgroup_name:
        cond = (cond & (SessionRow.scaling_group_name == sgroup_name))
    query = (
        sa.select(SessionRow)
        .where(cond)
    )
    if load_intrinsic:
        query = query.options(
            noload('*'),
            selectinload(SessionRow.image).noload('*'),
            selectinload(SessionRow.kernels)
            .options(
                noload('*'),
                selectinload(KernelRow.image).noload('*'),
                selectinload(KernelRow.agent).noload('*'),
            ),
        )
    if do_ordering:
        query = query.order_by(SessionRow.created_at)
    result = await db_session.execute(query)
    return result.scalars().all()


async def update_session_kernels(
    db_session: SASession,
    session: Union[SessionRow, SessionId],
    *,
    kernel_data: Mapping[str, Any],
    extra_cond=None,
    sess_cond=None,
) -> None:
    """
    Update kernels which in a specific session first,
    then update the session those kernels are in.
    """

    if isinstance(session, SessionRow):
        session_id = session.id
    elif isinstance(session, UUID):
        session_id = session
    else:
        raise RuntimeError(
            'Invalid time of session. '
            f'expect SessionRow, uuid.UUID type, but got {type(session)}')

    sess_cols = SessionRow.__mapper__.columns
    session_update = {
        k: v for k, v in kernel_data.items() if k in sess_cols
    }
    if 'status' in kernel_data:
        session_update['status'] = \
            _KERNEL_SESSION_STATUS_MAPPING[kernel_data['status']]

    async with db_session.begin_nested():
        cond = (KernelRow.session_id == session_id)
        if extra_cond is not None:
            cond = cond & extra_cond
        update_query = (
            sa.update(KernelRow)
            .values(**kernel_data)
            .where(cond)
        )
        await db_session.execute(update_query)
        await db_session.flush()

        if not session_update:
            return
        cond = (SessionRow.id == session_id)
        if sess_cond is not None:
            cond = cond & sess_cond

        update_query = (
            sa.update(SessionRow)
            .values(**session_update)
            .where(cond)
        )
        await db_session.execute(update_query)
        await db_session.commit()


async def update_kernel(
    db_session: SASession,
    kernel: Union[KernelRow, KernelId],
    *,
    kernel_data: Mapping[str, Any],
    extra_cond=None,
) -> None:
    if isinstance(kernel, KernelRow):
        kernel_id = kernel.id
    elif isinstance(kernel, UUID):
        kernel_id = kernel
    else:
        raise RuntimeError(
            'Invalid time of session. '
            f'expect KernelRow, uuid.UUID type, but got {type(kernel)}')

    sess_attr = SessionRow.__dict__
    session_update = {
        k: v for k, v in kernel_data.items() if k in sess_attr
    }
    if 'status' in kernel_data:
        session_update['status'] = \
            _KERNEL_SESSION_STATUS_MAPPING[kernel_data['status']]

    async with db_session.begin_nested():
        cond = (KernelRow.id == kernel_id)
        if extra_cond is not None:
            cond = cond & extra_cond
        update_query = (
            sa.update(KernelRow)
            .values(**kernel_data)
            .where(cond)
        )
        await db_session.execute(update_query)

        if not session_update:
            return

        fetch_query = (
            sa.select(KernelRow.session_id)
            .where(cond)
        )
        result = await db_session.execute(fetch_query)
        session_id = result.scalar()
        update_query = (
            sa.update(SessionRow)
            .values(**session_update)
            .where(SessionRow.id == session_id)
        )
        await db_session.execute(update_query)
        await db_session.commit()


async def enqueue_session(
    db_session: SASession,
    access_key: AccessKey,
    session_data: Mapping[str, Any],
    kernel_data: Sequence[Mapping[str, Any]],
    dependency_sessions: Sequence[SessionId] = None,
) -> SessionId:
    session = SessionRow(**session_data)
    async with db_session.begin_nested():
        db_session.add(session)
        db_session.add_all((KernelRow(**kernel) for kernel in kernel_data))
        session_id = SessionId(session.id)

        if not dependency_sessions:
            await db_session.commit()
            return session_id

        matched_dependency_session_ids = []
        for dependency_id in dependency_sessions:
            match_info = await match_sessions(
                db_session, dependency_id, access_key,
            )
            try:
                depend_id = match_info[0].id
            except IndexError:
                raise UnknownDependencySession(dependency_id)
            matched_dependency_session_ids.append(depend_id)
        dependency_rows = [SessionDependencyRow(session_id=session_id, depends_on=depend_id)
            for depend_id in matched_dependency_session_ids]
        db_session.add_all(dependency_rows)

        await db_session.commit()
    return session_id


async def get_sgroup_managed_sessions(
    db_sess: SASession,
    sgroup_name: str,
) -> List[SessionRow]:
    candidate_statues = (SessionStatus.PENDING, *AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES)
    query = (
        sa.select(SessionRow)
        .where((SessionRow.scaling_group_name == sgroup_name) & (SessionRow.status.in_(candidate_statues)))
        .options(
            noload('*'),
            selectinload(SessionRow.group).options(noload('*')),
            selectinload(SessionRow.domain).options(noload('*')),
            selectinload(SessionRow.access_key).options(noload('*')),
        )
    )
    result = await db_sess.execute(query)
    return result.scalars().all()


async def get_schedulerable_session(
    db_sess: SASession,
    session_id: SessionId,
) -> SessionRow:
    sess = await db_sess.get(
        SessionRow, session_id,
        populate_existing=True,
        options=(
            noload('*'),
            selectinload(SessionRow.image).noload('*'),
            selectinload(SessionRow.kernels)
            .options(
                noload('*'),
                selectinload(KernelRow.image).noload('*'),
                selectinload(KernelRow.agent).noload('*'),
            ),
        ),
    )
    return sess


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


async def check_all_dependencies(
    db_session: SASession,
    sess_ctx: SessionRow,
) -> Tuple[bool, Optional[str]]:
    j = sa.join(
        SessionDependencyRow,
        SessionRow,
        SessionDependencyRow.depends_on == SessionDependencyRow.session_id,
    )
    query = (
        sa.select(SessionRow.id, SessionRow.name, SessionRow.result)
        .select_from(j)
        .where(SessionDependencyRow.session_id == sess_ctx.id)
    )
    result = await db_session.execute(query)
    rows = result.scalars().all()
    pending_dependencies = [sess_row for sess_row in rows if sess_row.result != SessionResult.SUCCESS]
    all_success = (not pending_dependencies)
    if all_success:
        return (True, None)
    return (
        False,
        "Waiting dependency sessions to finish as success. ({})".format(
            ", ".join(f"{sess_row.name} ({sess_row.session_id})" for sess_row in pending_dependencies),
        ),
    )
