from __future__ import annotations

import enum
import functools
from datetime import datetime
from typing import Any, List, Mapping, Sequence, TypedDict, Union
from uuid import UUID

import sqlalchemy as sa
from dateutil.tz import tzutc
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
    MainKernelNotFound,
    TooManyKernelsFound,
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
from .kernel import DEAD_KERNEL_STATUSES, KernelRow, KernelStatus
from .keypair import KeyPairRow

__all__ = (
    'SessionStatus',
    'DEAD_SESSION_STATUSES',
    'AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES',
    'USER_RESOURCE_OCCUPYING_SESSION_STATUSES',
    'SessionRow', 'enqueue_session', 'get_sgroup_managed_sessions',
    'update_kernel_status', 'update_session_with_kernels',
    'get_scheduled_sessions', 'get_schedulerable_session',
    'match_sessions',
    'get_session_by_id',
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


def _translate_status_by_value(from_, to_: enum.EnumMeta):
    for s in to_:
        if s.value == from_.value:
            return s
    else:
        raise RuntimeError(f'Status `{from_}` does not match any status of `{to_}`')


KERNEL_SESSION_STATUS_MAPPING = {s: _translate_status_by_value(s, SessionStatus) for s in KernelStatus}

SESSION_KERNEL_STATUS_MAPPING = {s: _translate_status_by_value(s, KernelStatus) for s in SessionStatus}


def aggregate_kernel_status(kernel_statues: Sequence[KernelStatus]) -> SessionStatus:
    behind_most = kernel_statues[0]
    for s in kernel_statues:
        match s:
            case KernelStatus.ERROR:
                return SessionStatus.ERROR
            case KernelStatus.SUSPENDED:
                return SessionStatus.SUSPENDED
            case KernelStatus.CANCELLED:
                return SessionStatus.CANCELLED
            case _:
                behind_most = min(behind_most, s, key=lambda x: x.value)
    return KERNEL_SESSION_STATUS_MAPPING[behind_most]


class SessionOp(str, enum.Enum):
    CREATE = 'create_session'
    DESTROY = 'destroy_session'
    RESTART = 'restart_session'
    EXECUTE = 'execute'
    REFRESH = 'refresh_session'
    SHUTDOWN_SERVICE = 'shutdown_service'
    UPLOAD_FILE = 'upload_file'
    DOWNLOAD_FILE = 'download_file'
    LIST_FILE = 'list_files'
    GET_AGENT_LOGS = 'get_logs_from_agent'


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
    kernels = relationship('KernelRow', back_populates='session')

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
        kerns = tuple(kern for kern in self.kernels if kern.cluster_role == DEFAULT_ROLE)
        if len(kerns) > 1:
            raise TooManyKernelsFound(
                f'Session (id: {self.id}) '
                'has more than 1 main kernel.',
            )
        if len(kerns) == 0:
            raise MainKernelNotFound(
                f'Session (id: {self.id}) has no main kernel.',
            )
        return kerns[0]


class UpdatedStatus(TypedDict, total=False):
    status: SessionStatus | KernelStatus
    status_info: str
    session_status_data: sa.Function | Mapping
    kernel_status_data: sa.Function | Mapping
    status_changed: datetime.datetime
    terminated_at: datetime.datetime | None


async def match_sessions(
    db_session: SASession,
    session_name_or_id: Union[str, UUID],
    access_key: AccessKey,
    *,
    allow_prefix: bool = False,
    allow_stale: bool = True,
    for_update: bool = False,
    max_matches: int = 10,
    load_kernels: bool = False,
) -> List[SessionRow]:
    """
    Match the prefix of session ID or session name among the sessions
    that belongs to the given access key, and return the list of SessionRow.
    """

    query_list = [functools.partial(get_sessions_by_name, allow_prefix=allow_prefix)]
    try:
        UUID(session_name_or_id)
    except ValueError:
        pass
    else:
        query_list.append(functools.partial(match_sessions_by_id, allow_prefix=False))
        if allow_prefix:
            query_list.append(functools.partial(match_sessions_by_id, allow_prefix=True))

    for fetch_func in query_list:
        rows = await fetch_func(
            db_session, session_name_or_id, access_key,
            allow_stale=allow_stale, for_update=for_update,
            max_matches=max_matches, load_kernels=load_kernels,
        )
        if not rows:
            continue
        return rows
    return []


def _build_session_fetch_query(
    base_cond,
    access_key: AccessKey | None = None,
    *,
    max_matches: int | None,
    allow_stale: bool = True,
    for_update: bool = False,
    do_ordering: bool = False,
    load_kernels: bool = False,
):
    cond = base_cond
    if access_key:
        cond = cond & (SessionRow.kp_access_key == access_key)
    if not allow_stale:
        cond = cond & (~SessionRow.status.in_(DEAD_SESSION_STATUSES))
    query = (
        sa.select(SessionRow)
        .where(cond)
        .order_by(sa.desc(SessionRow.created_at))
        .execution_options(populate_existing=True)
    )
    if max_matches:
        query = query.limit(max_matches).offset(0)
    if for_update:
        query = query.with_for_update()
    if do_ordering:
        query = query.order_by(SessionRow.created_at)

    query = query.options(
        noload('*'),
        selectinload(SessionRow.image).noload('*'),
    )
    if load_kernels:
        query = query.options(
            noload('*'),
            selectinload(SessionRow.kernels)
            .options(
                noload('*'),
                selectinload(KernelRow.image).noload('*'),
                selectinload(KernelRow.agent).noload('*'),
            ),
        )

    return query


async def match_sessions_by_id(
    db_session: SASession,
    session_id: SessionId,
    access_key: AccessKey | None = None,
    *,
    max_matches: int | None = None,
    allow_prefix: bool = False,
    allow_stale: bool = True,
    for_update: bool = False,
    load_kernels: bool = False,
) -> List[SessionRow]:
    if allow_prefix:
        cond = (sa.sql.expression.cast(SessionRow.id, sa.String).like(f'{session_id}%'))
    else:
        cond = (SessionRow.id == session_id)
    query = _build_session_fetch_query(
        cond, access_key,
        max_matches=max_matches,
        allow_stale=allow_stale,
        for_update=for_update,
        load_kernels=load_kernels,
    )

    result = await db_session.execute(query)
    return result.scalars().all()


async def get_session_by_id(
    db_session: SASession,
    session_id: SessionId,
    access_key: AccessKey | None = None,
    *,
    max_matches: int | None = None,
    allow_stale: bool = True,
    for_update: bool = False,
    load_kernels: bool = False,
) -> SessionRow | None:
    sessions = await match_sessions_by_id(
        db_session, session_id, access_key,
        max_matches, allow_stale, for_update,
        load_kernels, allow_prefix=False,
    )
    try:
        return sessions[0]
    except IndexError:
        return None


async def get_sessions_by_name(
    db_session: SASession,
    session_name: str,
    access_key: AccessKey,
    *,
    max_matches: int | None,
    allow_prefix: bool = False,
    allow_stale: bool = True,
    for_update: bool = False,
    load_kernels: bool = False,
) -> List[SessionRow]:
    if allow_prefix:
        cond = (sa.sql.expression.cast(SessionRow.name, sa.String).like(f'{session_name}%'))
    else:
        cond = (SessionRow.name == session_name)
    query = _build_session_fetch_query(
        cond, access_key,
        max_matches=max_matches,
        allow_stale=allow_stale,
        for_update=for_update,
        load_kernels=load_kernels,
    )
    result = await db_session.execute(query)
    return result.scalars().all()


async def get_scheduled_sessions(
    db_session: SASession,
) -> SessionRow:
    now = datetime.now(tzutc())
    update_data = {
        'status': SessionStatus.PREPARING,
        'status_changed': now,
        'status_info': "",
        'status_data': {},
    }
    query = (
        sa.update(SessionRow)
        .where(SessionRow.status == SessionStatus.SCHEDULED)
        .values(**update_data)
        .returning(SessionRow.id)
    )
    result = await db_session.execute(query)
    session_ids = result.all()

    update_data['status'] = KernelStatus.PREPARING

    query = (
        sa.update(KernelRow)
        .where(KernelRow.session_id.in_(session_ids))
        .values(**update_data)
    )
    await db_session.execute(query)

    query = (
        sa.select(SessionRow)
        .where(SessionRow.id.in_(session_ids))
        .order_by(SessionRow.created_at)
        .options(
            noload('*'),
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
    )
    result = await db_session.execute(query)
    return result.scalars().all()


async def update_session_with_kernels(
    db_session: SASession,
    session: Union[SessionRow, SessionId],
    access_key=None,
    *,
    update_data: UpdatedStatus,
    update_stale=False,
) -> None:
    """
    Update a certain session and then update all sibling kernels related to the given compute session.
    """

    if isinstance(session, SessionRow):
        session_id = session.id
    elif isinstance(session, UUID):
        session_id = session
    else:
        raise RuntimeError(
            'Invalid type of session. '
            f'expect SessionRow, uuid.UUID type, but got {type(session)}')

    if update_data.get('status') in (SessionStatus.CANCELLED, SessionStatus.TERMINATED):
        update_data['terminated_at'] = datetime.now(tzutc())

    kernel_update = {**update_data}

    def filter_status_data_keys(status_data, real_data_key, other_key):
        if real_data_key in status_data:
            status_data['status_data'] = status_data.pop(real_data_key)
        if other_key in status_data:
            del status_data[other_key]

    filter_status_data_keys(kernel_update, 'kernel_status_data', 'session_status_data')
    filter_status_data_keys(update_data, 'session_status_data', 'kernel_status_data')

    if session_status := update_data.get('status'):
        kernel_update['status'] = SESSION_KERNEL_STATUS_MAPPING[session_status]

    kern_cond = (KernelRow.session_id == session_id)
    sess_cond = (SessionRow.id == session_id)
    if access_key:
        kern_cond = kern_cond & (KernelRow.access_key == access_key)
        sess_cond = sess_cond & (SessionRow.kp_access_key == access_key)
    if not update_stale:
        kern_cond = kern_cond & ~(KernelRow.status.in_(DEAD_KERNEL_STATUSES))
        sess_cond = sess_cond & ~(SessionRow.status.in_(DEAD_SESSION_STATUSES))

    async with db_session.begin_nested():
        query = (
            sa.update(SessionRow)
            .where(sess_cond)
            .values(**update_data)
        )
        await db_session.execute(query)

        if not kernel_update:
            return

        update_query = (
            sa.update(KernelRow)
            .where(kern_cond)
            .values(**kernel_update)
        )
        await db_session.execute(update_query)


async def update_kernel_status(
    db_session: SASession,
    kernel: Union[KernelRow, KernelId],
    access_key=None,
    *,
    update_data: UpdatedStatus,
    only_active: bool = True,
    is_single_kernel: bool = False,
) -> None:
    """
    Update status of a kernel and update the data to the session which the kernel belongs to.
    """

    if isinstance(kernel, KernelRow):
        kernel_id = kernel.id
        session_id = kernel.session_id
    elif isinstance(kernel, UUID):
        kernel_id = kernel
        session_id = None
    else:
        raise RuntimeError(
            'Invalid type of kernel. '
            f'expect KernelRow, uuid.UUID type, but got {type(kernel)}')

    if update_data.get('status') in (KernelStatus.CANCELLED, KernelStatus.TERMINATED):
        if 'terminated_at' not in update_data:
            update_data['terminated_at'] = update_data.get('status_changed') or datetime.now(tzutc())

    def build_condition(cond, ak_col, active_cond):
        if access_key:
            cond = cond & (ak_col == access_key)
        if only_active:
            cond = cond & active_cond
        return cond

    kern_cond = build_condition(
        (KernelRow.id == kernel_id),
        KernelRow.access_key,
        ~(KernelRow.status.in_(DEAD_KERNEL_STATUSES)),
    )

    if 'kernel_status_data' in update_data:
        update_data['status_data'] = update_data.pop('kernel_status_data')

    session_update = {}
    if is_single_kernel:
        if kernel_status := update_data.get('status'):
            session_update['status'] = KERNEL_SESSION_STATUS_MAPPING[kernel_status]

    if session_status_data := update_data.get('session_status_data'):
        session_update['status_data'] = session_status_data

    async with db_session.begin_nested():
        query = (
            sa.update(KernelRow)
            .where(kern_cond)
            .values(**update_data)
        )
        if session_id is None:
            query = query.returning(KernelRow.session_id)
            return_val = await db_session.execute(query)
            session_id = return_val.first()
        else:
            await db_session.execute(query)

        if session_update:
            sess_cond = build_condition(
                (SessionRow.id == session_id),
                SessionRow.kp_access_key,
                ~(SessionRow.status.in_(DEAD_SESSION_STATUSES)),
            )
            query = (
                sa.update(SessionRow)
                .where(sess_cond)
                .values(**session_update)
            )
            await db_session.execute(query)


async def enqueue_session(
    db_session: SASession,
    access_key: AccessKey,
    session_data: Mapping[str, Any],
    kernel_data: Sequence[Mapping[str, Any]],
    dependency_sessions: Sequence[SessionId] = None,
) -> SessionId:
    session = SessionRow(**session_data)
    kernels = [KernelRow(**kernel) for kernel in kernel_data]
    db_session.add(session)
    db_session.add_all(kernels)
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
) -> List[SessionRow]:
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
    return pending_dependencies
