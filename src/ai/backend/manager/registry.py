from __future__ import annotations

import asyncio
import copy
import itertools
import logging
import re
import secrets
import time
import uuid
import weakref
from collections import defaultdict
from contextlib import asynccontextmanager as actxmgr
from contextvars import ContextVar
from datetime import datetime
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

import aiodocker
import aioredis
import aiotools
import snappy
import sqlalchemy as sa
import zmq
from async_timeout import timeout as _timeout
from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport
from callosum.rpc import Peer, RPCUserError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dateutil.tz import tzutc
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession as SASession
from sqlalchemy.orm import noload, selectinload
from sqlalchemy.sql.expression import true
from yarl import URL

from ai.backend.common import msgpack, redis
from ai.backend.common.docker import ImageRef, get_known_registries, get_registry_info
from ai.backend.common.events import (
    AgentStartedEvent,
    KernelCancelledEvent,
    KernelTerminatedEvent,
    KernelTerminatingEvent,
    SessionCancelledEvent,
    SessionEnqueuedEvent,
    SessionStartedEvent,
    SessionTerminatedEvent,
)
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext
from ai.backend.common.service_ports import parse_service_ports
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    BinarySize,
    ClusterInfo,
    ClusterMode,
    ClusterSSHKeyPair,
    DeviceId,
    HardwareMetadata,
    KernelEnqueueingConfig,
    KernelId,
    RedisConnectionInfo,
    ResourceSlot,
    SessionEnqueuingConfig,
    SessionId,
    SessionResult,
    SessionTypes,
    SlotName,
    SlotTypes,
    check_typed_dict,
)
from ai.backend.common.utils import nmget

from .api.exceptions import (
    AgentError,
    BackendError,
    GenericForbidden,
    InstanceNotFound,
    InvalidAPIParameters,
    KernelCreationFailed,
    KernelDestructionFailed,
    KernelExecutionFailed,
    KernelRestartFailed,
    RejectedByHook,
    ScalingGroupNotFound,
    SessionNotFound,
    TooManySessionsMatched,
    UnknownDependencySession,
)
from .config import SharedConfig
from .defs import DEFAULT_ROLE, INTRINSIC_SLOTS
from .exceptions import MultiAgentError
from .models import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    AGENT_UPDATE_FIELDS,
    DEAD_KERNEL_STATUSES,
    USER_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    UpdatedStatus,
    AgentRow,
    AgentStatus,
    ImageRow,
    KernelStatus,
    SessionStatus,
    agents,
    get_agent_cols,
    kernels,
    prepare_dotfiles,
    prepare_vfolder_mounts,
    query_allowed_sgroups,
    recalc_agent_resource_occupancy,
    recalc_concurrency_used,
)
from .models.kernel import KernelRow, get_kernel_occupancy
from .models.session import (
    SessionRow,
    aggregate_kernel_status,
    enqueue_session,
    match_sessions,
    update_kernel_status,
)
from .models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
    reenter_txn,
    reenter_txn_session,
    sql_json_merge,
)
from .types import SessionGetter, UserScope

if TYPE_CHECKING:
    from sqlalchemy.engine.row import Row
    from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

    from ai.backend.common.events import EventDispatcher, EventProducer

    from .models import ScalingGroupRow
    from .models.storage import StorageSessionManager
    from .scheduler.types import KernelAgentBinding, SchedulingContext

__all__ = ['AgentRegistry', 'InstanceNotFound']

log = BraceStyleAdapter(logging.getLogger('ai.backend.manager.registry'))

_read_only_txn_opts = {
    'postgresql_readonly': True,
}


class PeerInvoker(Peer):

    class _CallStub:

        _cached_funcs: Dict[str, Callable]
        order_key: ContextVar[Optional[str]]

        def __init__(self, peer: Peer):
            self._cached_funcs = {}
            self.peer = peer
            self.order_key = ContextVar('order_key', default=None)

        def __getattr__(self, name: str):
            if f := self._cached_funcs.get(name, None):
                return f
            else:
                async def _wrapped(*args, **kwargs):
                    request_body = {
                        'args': args,
                        'kwargs': kwargs,
                    }
                    self.peer.last_used = time.monotonic()
                    ret = await self.peer.invoke(name, request_body,
                                                 order_key=self.order_key.get())
                    self.peer.last_used = time.monotonic()
                    return ret
                self._cached_funcs[name] = _wrapped
                return _wrapped

    call: _CallStub
    last_used: float

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.call = self._CallStub(self)
        self.last_used = time.monotonic()


@actxmgr
async def RPCContext(
    agent_id: AgentId,
    addr,
    *,
    invoke_timeout: float = None,
    order_key: str = None,
    keepalive_timeout: int = 60,
) -> AsyncIterator[PeerInvoker]:
    keepalive_retry_count = 3
    keepalive_interval = keepalive_timeout // keepalive_retry_count
    if keepalive_interval < 2:
        keepalive_interval = 2
    peer = PeerInvoker(
        connect=ZeroMQAddress(addr),
        transport=ZeroMQRPCTransport,
        transport_opts={
            'zsock_opts': {
                zmq.TCP_KEEPALIVE: 1,
                zmq.TCP_KEEPALIVE_IDLE: keepalive_timeout,
                zmq.TCP_KEEPALIVE_INTVL: keepalive_interval,
                zmq.TCP_KEEPALIVE_CNT: keepalive_retry_count,
            },
        },
        serializer=msgpack.packb,
        deserializer=msgpack.unpackb,
    )
    try:
        with _timeout(invoke_timeout):
            async with peer:
                okey_token = peer.call.order_key.set('')
                try:
                    yield peer
                finally:
                    peer.call.order_key.reset(okey_token)
    except RPCUserError as orig_exc:
        raise AgentError(agent_id, orig_exc.name, orig_exc.repr, orig_exc.args)
    except Exception:
        raise


class AgentRegistry:
    """
    Provide a high-level API to create, destroy, and query the computation
    kernels.

    The registry is also responsible to implement our resource management
    policy, such as the limitation of maximum number of kernels per instance.
    """

    kernel_creation_tracker: Dict[KernelId, asyncio.Future]
    _post_kernel_creation_tasks: weakref.WeakValueDictionary[KernelId, asyncio.Task]
    _post_kernel_creation_infos: dict[KernelId, asyncio.Future]
    _kernel_actual_allocated_resources: dict[KernelId, ResourceSlot]

    def __init__(
        self,
        shared_config: SharedConfig,
        db: ExtendedAsyncSAEngine,
        redis_stat: RedisConnectionInfo,
        redis_live: RedisConnectionInfo,
        redis_image: RedisConnectionInfo,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        storage_manager: StorageSessionManager,
        hook_plugin_ctx: HookPluginContext,
    ) -> None:
        self.shared_config = shared_config
        self.docker = aiodocker.Docker()
        self.db = db
        self.redis_stat = redis_stat
        self.redis_live = redis_live
        self.redis_image = redis_image
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.storage_manager = storage_manager
        self.hook_plugin_ctx = hook_plugin_ctx
        self.kernel_creation_tracker = {}
        self._post_kernel_creation_tasks = weakref.WeakValueDictionary()
        self._post_kernel_creation_infos = {}
        self._kernel_actual_allocated_resources = {}
        self.rpc_keepalive_timeout = \
            int(shared_config.get("config/network/rpc/keepalive-timeout", "60"))

    async def init(self) -> None:
        self.heartbeat_lock = asyncio.Lock()

    async def shutdown(self) -> None:
        pass

    async def get_instance(self, inst_id: AgentId, field=None):
        async with self.db.begin_readonly() as conn:
            cols = [agents.c.id]
            if field is not None:
                cols.append(field)
            query = (sa.select(cols)
                       .select_from(agents)
                       .where(agents.c.id == inst_id))
            result = await conn.execute(query)
            row = result.first()
            if not row:
                raise InstanceNotFound(inst_id)
            return row

    async def enumerate_instances(self, check_shadow=True):

        async with self.db.begin_readonly() as conn:
            query = (sa.select('*').select_from(agents))
            if check_shadow:
                query = query.where(agents.c.status == AgentStatus.ALIVE)
            async for row in (await conn.stream(query)):
                yield row

    async def update_instance(self, inst_id, updated_fields):

        async def _update() -> None:
            async with self.db.begin() as conn:
                query = (
                    sa.update(agents)
                    .values(**updated_fields)
                    .where(agents.c.id == inst_id)
                )
                await conn.execute(query)

        await execute_with_retry(_update)

    async def gather_agent_hwinfo(self, instance_id: AgentId) -> Mapping[str, HardwareMetadata]:
        agent = await self.get_instance(instance_id, agents.c.addr)
        async with RPCContext(
            agent['id'], agent['addr'],
            invoke_timeout=None,
            keepalive_timeout=self.rpc_keepalive_timeout,
        ) as rpc:
            result = await rpc.call.gather_hwinfo()
            return {
                k: check_typed_dict(v, HardwareMetadata)  # type: ignore  # (python/mypy#9827)
                for k, v in result.items()
            }

    async def gather_storage_hwinfo(self, vfolder_host: str) -> HardwareMetadata:
        proxy_name, volume_name = self.storage_manager.split_host(vfolder_host)
        async with self.storage_manager.request(
            proxy_name, 'GET', 'volume/hwinfo',
            json={'volume': volume_name},
            raise_for_status=True,
        ) as (_, storage_resp):
            return check_typed_dict(
                await storage_resp.json(), HardwareMetadata,  # type: ignore  # (python/mypy#9827)
            )

    @actxmgr
    async def handle_kernel_exception(
        self,
        op: str,
        kernel_id: KernelId,
        access_key: AccessKey,
        error_callback=None,
        cancellation_callback=None,
        set_error: bool = False,
    ) -> AsyncIterator[None]:
        op_exc = {
            'create_session': KernelCreationFailed,
            'restart_session': KernelRestartFailed,
            'destroy_session': KernelDestructionFailed,
            'execute': KernelExecutionFailed,
            'shutdown_service': KernelExecutionFailed,
            'upload_file': KernelExecutionFailed,
            'download_file': KernelExecutionFailed,
            'list_files': KernelExecutionFailed,
            'get_logs_from_agent': KernelExecutionFailed,
            'refresh_session': KernelExecutionFailed,
        }
        exc_class = op_exc[op]
        # NOTE: Error logging is done outside of this actxmanager.
        try:
            yield
        except asyncio.TimeoutError:
            if set_error:
                await self.set_session_kernel_status(
                    kernel_id,
                    access_key,
                    status=KernelStatus.ERROR,
                    status_info=f'operation-timeout ({op})',
                )
            if error_callback:
                await error_callback()
            raise exc_class('TIMEOUT') from None
        except asyncio.CancelledError:
            if cancellation_callback:
                await cancellation_callback()
            raise
        except AgentError as e:
            if set_error:
                await self.set_session_kernel_status(
                    kernel_id,
                    access_key,
                    status=KernelStatus.ERROR,
                    status_info=f'agent-error ({e!r})',
                    status_data={
                        "error": {
                            "src": "agent",
                            "agent_id": e.agent_id,
                            "name": e.exc_name,
                            "repr": e.exc_repr,
                        },
                    },
                )
            if error_callback:
                await error_callback()
            raise exc_class('FAILURE', e) from None
        except BackendError:
            # silently re-raise to make them handled by gateway http handlers
            raise
        except Exception as e:
            if set_error:
                await self.set_session_kernel_status(
                    kernel_id,
                    access_key,
                    status=KernelStatus.ERROR,
                    status_info=f'other-error ({e!r})',
                    status_data={
                        "error": {
                            "src": "other",
                            "name": e.__class__.__name__,
                            "repr": repr(e),
                        },
                    },
                )
            if error_callback:
                await error_callback()
            raise

    async def get_kernel(
        self,
        kern_id: uuid.UUID,
        field=None,
        allow_stale: bool = False,
        db_connection=None,
    ):
        """
        Retrieve the kernel information from the given kernel ID.
        This ID is unique for all individual agent-spawned containers.

        If ``field`` is given, it extracts only the raw value of the given
        field, without wrapping it as Kernel object.
        If ``allow_stale`` is true, it skips checking validity of the kernel
        owner instance.
        """
        cols = [kernels.c.id, kernels.c.session_id,
                kernels.c.agent_addr, kernels.c.kernel_host, kernels.c.access_key]
        if field == '*':
            cols = [sa.text('*')]
        elif isinstance(field, (tuple, list)):
            cols.extend(field)
        elif isinstance(field, (sa.Column, sa.sql.elements.ColumnClause)):
            cols.append(field)
        elif isinstance(field, str):
            cols.append(sa.column(field))
        async with reenter_txn(self.db, db_connection, _read_only_txn_opts) as conn:
            if allow_stale:
                query = (
                    sa.select(cols)
                    .select_from(kernels)
                    .where(kernels.c.id == kern_id)
                    .limit(1).offset(0))
            else:
                query = (
                    sa.select(cols)
                    .select_from(kernels.join(agents))
                    .where(
                        (kernels.c.id == kern_id) &
                        ~(kernels.c.status.in_(DEAD_KERNEL_STATUSES)) &
                        (agents.c.status == AgentStatus.ALIVE) &
                        (agents.c.id == kernels.c.agent),
                    )
                    .limit(1).offset(0))
            result = await conn.execute(query)
            row = result.first()
            if row is None:
                raise SessionNotFound
            return row

    async def get_kernels(
        self,
        session_name_or_id: Union[str, uuid.UUID],
        access_key: str, *,
        field=None,
        allow_stale: bool = False,
        for_update: bool = False,
        db_connection: SAConnection = None,
        cluster_role: str = None,
    ) -> Sequence[sa.engine.Row]:
        """
        Retrieve the kernel information by kernel's ID, kernel's session UUID
        (session_id), or kernel's name (session_id) paired with access_key.
        If the session is composed of multiple containers, this will return
        every container information, unless field and role is specified by the caller.

        :param session_name_or_id: kernel's id, session_id (session name), or session_id.
        :param access_key: Access key used to create kernels.
        :param field: If given, it extracts only the raw value of the given field, without
                      wrapping it as Kernel object.
        :param allow_stale: If True, filter "inactive" kernels as well as "active" ones.
                            If False, filter "active" kernels only.
        :param for_update: Apply for_update during select query.
        :param db_connection: Database connection for reuse.
        :param cluster_role: Filter kernels by role. "main", "sub", or None (all).
        """
        cols = [
            kernels.c.id,
            kernels.c.session_id,
            kernels.c.session_name,
            kernels.c.session_type,
            kernels.c.status,
            kernels.c.cluster_mode,
            kernels.c.cluster_role,
            kernels.c.cluster_idx,
            kernels.c.access_key,
            kernels.c.agent_addr,
            kernels.c.kernel_host,
            kernels.c.image_id,
            kernels.c.registry,
            kernels.c.service_ports,
        ]
        if field == '*':
            cols = [sa.text('*')]
        elif isinstance(field, (tuple, list)):
            cols.extend(field)
        elif isinstance(field, (sa.Column, sa.sql.elements.ColumnClause)):
            cols.append(field)
        elif isinstance(field, str):
            cols.append(sa.column(field))

        cond_id = (
            (sa.sql.expression.cast(kernels.c.id, sa.String).like(f'{session_name_or_id}%')) &
            (kernels.c.access_key == access_key)
        )
        cond_name = (
            (kernels.c.session_name.like(f'{session_name_or_id}%')) &
            (kernels.c.access_key == access_key)
        )
        cond_session_id = (
            (sa.sql.expression.cast(kernels.c.session_id, sa.String).like(f'{session_name_or_id}%')) &
            (kernels.c.access_key == access_key)
        )
        if cluster_role is not None:
            cond_id = cond_id & (kernels.c.cluster_role == cluster_role)
            cond_name = cond_name & (kernels.c.cluster_role == cluster_role)
            cond_session_id = cond_session_id & (kernels.c.cluster_role == cluster_role)
        if allow_stale:
            cond_status = true()  # any status
        else:
            cond_status = ~(kernels.c.status.in_(DEAD_KERNEL_STATUSES))
        query_by_id = (
            sa.select(cols)
            .select_from(kernels)
            .where(cond_id & cond_status)
            .order_by(sa.desc(kernels.c.created_at))
            .limit(10).offset(0)
        )
        if for_update:
            query_by_id = query_by_id.with_for_update()
        query_by_name = (
            sa.select(cols)
            .select_from(kernels)
            .where(cond_name & cond_status)
            .order_by(sa.desc(kernels.c.created_at))
        )
        if for_update:
            query_by_name = query_by_name.with_for_update()
        query_by_session_id = (
            sa.select(cols)
            .select_from(kernels)
            .where(cond_session_id & cond_status)
            .order_by(sa.desc(kernels.c.created_at))
            .limit(10).offset(0)
        )
        if for_update:
            query_by_session_id = query_by_session_id.with_for_update()
        if allow_stale:
            query_by_name = query_by_name.limit(10).offset(0)
        else:
            # for backward-compatibility
            query_by_name = query_by_name.limit(1).offset(0)

        async with reenter_txn(self.db, db_connection) as conn:
            for query in [
                query_by_id,
                query_by_session_id,
                query_by_name,
            ]:
                result = await conn.execute(query)
                if result.rowcount == 0:
                    continue
                return result.fetchall()
        raise SessionNotFound

    async def get_session_by_session_id(
        self,
        session_id: SessionId,
        *,
        db_connection: SAConnection,
        for_update: bool = False,
    ) -> sa.engine.Row:
        query = (
            sa.select(
                [sa.text('*')],
            )
            .select_from(kernels)
            .where(
                (kernels.c.session_id == session_id) &
                (kernels.c.cluster_role == DEFAULT_ROLE),
            )
        )
        if for_update:
            query = query.with_for_update()
        result = await db_connection.execute(query)
        row = result.first()
        if row is None:
            raise SessionNotFound
        return row

    async def get_session_by_kernel_id(
        self,
        kernel_id: KernelId,
        *,
        db_connection: SAConnection,
        for_update: bool = False,
    ) -> sa.engine.Row:
        query = (
            sa.select(
                [sa.text('*')],
            )
            .select_from(kernels)
            .where(
                (kernels.c.session_id == (
                    sa.select([kernels.c.session_id])
                    .select_from(kernels)
                    .where(kernels.c.id == kernel_id)
                )) &
                (kernels.c.cluster_role == DEFAULT_ROLE),
            )
        )
        if for_update:
            query = query.with_for_update()
        result = await db_connection.execute(query)
        row = result.first()
        if row is None:
            raise SessionNotFound
        return row

    async def get_session(
        self,
        session_name_or_id: Union[str, uuid.UUID],
        access_key: Union[str, AccessKey],
        *,
        allow_stale: bool = False,
        for_update: bool = False,
        load_kernels: bool = False,
        db_session: SASession = None,
    ) -> SessionRow:
        """
        Retrieve the session information by session's ID, kernel's session UUID
        (session_id), or session's name (session_id) paired with access_key.
        If the session is composed of multiple containers, this will return
        the information of the main kernel.

        :param session_name_or_id: kernel's id, session_id (session name), or session_id.
        :param access_key: Access key used to create kernels.
        :param field: If given, it extracts only the raw value of the given field, without
                      wrapping it as Kernel object.
        :param allow_stale: If True, filter "inactive" kernels as well as "active" ones.
                            If False, filter "active" kernels only.
        :param for_update: Apply for_update during select query.
        :param load_kernels: Load related kernels eagerly.
        :param db_connection: Database connection for reuse.
        """
        async with reenter_txn_session(self.db, db_session, read_only=True) as db_sess:
            sess_rows = await match_sessions(
                db_sess,
                session_name_or_id,
                AccessKey(access_key),
                allow_prefix=True,
                allow_stale=allow_stale,
                for_update=for_update,
                load_kernels=load_kernels,
            )
            if not sess_rows:
                raise SessionNotFound()
            if len(sess_rows) > 1:
                raise TooManySessionsMatched(extra_data={'matches': sess_rows})
            return sess_rows[0]

    async def get_session_by_id(
        self,
        session_id: uuid.UUID,
        db_session: SASession | None = None,
    ) -> SessionRow:
        async with reenter_txn_session(self.db, db_session, read_only=True) as db_sess:
            return await db_sess.get(
                SessionRow, session_id,
            )

    async def get_session_main_kernel(
        self,
        session_name_or_id: Union[str, uuid.UUID],
        access_key: Union[str, AccessKey],
        *,
        allow_stale: bool = False,
        for_update: bool = False,
        db_session: SASession = None,
    ) -> KernelRow:
        sess = await self.get_session(
            session_name_or_id, access_key,
            allow_stale=allow_stale, for_update=for_update,
            load_kernels=True, db_session=db_session,
        )
        return sess.main_kernel

    async def get_session_kernels(
        self,
        session_id: str,
        access_key: str, *,
        field=None,
        allow_stale: bool = False,
        for_update: bool = False,
        db_connection: SAConnection = None,
        cluster_role: str = None,
    ) -> Sequence[sa.engine.Row]:
        """
        Retrieve the information of all kernels of a session by session UUID.
        If the session is bundled with multiple containers,
        this will return every information of them.

        :param session_id: Session's UUID.
        :param access_key: Access key used to create the session.
        :param field: If given, it extracts only the raw value of the given field, without
                      wrapping it as Kernel object.
        :param allow_stale: If True, filter "inactive" kernels as well as "active" ones.
                            If False, filter "active" kernels only.
        :param for_update: Apply for_update during select query.
        :param db_connection: Database connection for reuse.
        :param cluster_role: Filter kernels by role. "main", "sub", or None (all).
        """
        return await self.get_kernels(
            session_id, access_key,
            field=field, for_update=for_update,
            db_connection=db_connection,
            cluster_role=cluster_role,
        )

    async def enqueue_session(
        self,
        session_creation_id: str,
        session_name: str,
        access_key: AccessKey,
        session_enqueue_configs: SessionEnqueuingConfig,
        scaling_group_name: Optional[str],
        session_type: SessionTypes,
        resource_policy,    # type: ignore
        *,
        user_scope: UserScope,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        cluster_size: int = 1,
        session_tag: str = None,
        internal_data: dict = None,
        starts_at: datetime = None,
        agent_list: Sequence[AgentId] = None,
        dependency_sessions: Sequence[SessionId] = None,
        callback_url: URL = None,
    ) -> SessionId:

        kernel_enqueue_configs = session_enqueue_configs['kernel_configs']
        session_creation_config = session_enqueue_configs['creation_config']
        session_image = session_enqueue_configs['image_ref']
        session_id = SessionId(uuid.uuid4())

        async with self.db.begin_readonly() as conn:
            # Check scaling group availability if scaling_group parameter is given.
            # If scaling_group is not provided, it will be selected as the first one among
            # the list of allowed scaling groups.
            sgroups: List[ScalingGroupRow]
            sgroups = await query_allowed_sgroups(
                SASession(conn), user_scope.domain_name, user_scope.group_id, access_key,
            )
            if not sgroups:
                raise ScalingGroupNotFound("You have no scaling groups allowed to use.")

            if scaling_group_name is None:
                scaling_group_name = sgroups[0].name
                log.warning(
                    f"enqueue_session(s:{session_name}, ak:{access_key}): "
                    f"The client did not specify the scaling group for session; "
                    f"falling back to {scaling_group_name}",
                )
            else:
                if all(sgroup.name != scaling_group_name for sgroup in sgroups):
                    raise ScalingGroupNotFound(f"The scaling group {scaling_group_name} does not exist.")
            assert scaling_group_name is not None

            # Translate mounts/mount_map into vfolder mounts
            requested_mounts = session_creation_config.get('mounts') or []
            requested_mount_map = session_creation_config.get('mount_map') or {}
            allowed_vfolder_types = await self.shared_config.get_vfolder_types()
            vfolder_mounts = await prepare_vfolder_mounts(
                conn,
                self.storage_manager,
                allowed_vfolder_types,
                user_scope,
                requested_mounts,
                requested_mount_map,
            )

            # Prepare internal data for common dotfiles.
            dotfile_data = await prepare_dotfiles(
                conn,
                user_scope,
                access_key,
                vfolder_mounts,
            )

        is_multicontainer = cluster_size > 1
        if is_multicontainer:
            if len(kernel_enqueue_configs) == 1:
                log.debug(
                    'enqueue_session(): replicating kernel_enqueue_config with cluster_size={}',
                    cluster_size,
                )
                # the first kernel_config is repliacted to sub-containers
                replicated = kernel_enqueue_configs[0]
                assert replicated['cluster_role'] == DEFAULT_ROLE
                replicated['cluster_idx'] = 1
                for i in range(cluster_size - 1):
                    sub_kernel_config = {
                        **replicated,
                        'cluster_role': 'sub',
                        'cluster_idx': i + 1,
                        'cluster_hostname': f'sub{i + 1}',
                    }
                    kernel_enqueue_configs.append(KernelEnqueueingConfig(**sub_kernel_config))
            elif len(kernel_enqueue_configs) > 1:
                # each container should have its own kernel_config
                if len(kernel_enqueue_configs) != cluster_size:
                    raise InvalidAPIParameters(
                        "The number of kernel configs differs from the cluster size")
                log.debug(
                    'enqueue_session(): using given kernel_enqueue_configs with cluster_size={}',
                    cluster_size,
                )
            else:
                raise InvalidAPIParameters("Missing kernel configurations")

        # fetch image data at once.
        image_map: Mapping[str, ImageRow]
        image_refs = [*[conf['image_ref'] for conf in kernel_enqueue_configs], session_image]
        async with self.db.begin_readonly_session() as session:
            log_msg = [f'image ref => {ref} ({ref.architecture})' for ref in image_refs]
            log.debug(
                'enqueue_session(): '
                ', '.join(log_msg),
            )
            image_map = await ImageRow.resolve_all(session, image_refs)

        session_data = {
            'id': session_id,
            'status': SessionStatus.PENDING,
            'creation_id': session_creation_id,
            'name': session_name,
            'session_type': session_type,
            'cluster_mode': cluster_mode.value,
            'cluster_size': cluster_size,
            'scaling_group_name': scaling_group_name,
            'domain_name': user_scope.domain_name,
            'group_id': user_scope.group_id,
            'user_uuid': user_scope.user_uuid,
            'kp_access_key': access_key,
            'tag': session_tag,
            'starts_at': starts_at,
            'callback_url': callback_url,
            'occupying_slots': ResourceSlot(),
            'requested_slots': ResourceSlot(),
            'vfolder_mounts': vfolder_mounts,
            'image_id': image_map[session_image.canonical].id,
        }

        # Prepare internal data.
        internal_data = {} if internal_data is None else internal_data
        internal_data.update(dotfile_data)

        hook_result = await self.hook_plugin_ctx.dispatch(
            'PRE_ENQUEUE_SESSION',
            (session_id, session_name, access_key),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)

        kernel_shared_data = {
            'status': KernelStatus.PENDING,
            'session_creation_id': session_creation_id,
            'session_id': session_id,
            'session_name': session_name,
            'session_type': session_type,
            'cluster_mode': cluster_mode.value,
            'cluster_size': cluster_size,
            'scaling_group': scaling_group_name,
            'domain_name': user_scope.domain_name,
            'group_id': user_scope.group_id,
            'user_uuid': user_scope.user_uuid,
            'access_key': access_key,
            'tag': session_tag,
            'starts_at': starts_at,
            'internal_data': internal_data,
            'callback_url': callback_url,
            'occupied_shares': {},
            'mounts': [  # TODO: keep for legacy?
                mount.name for mount in vfolder_mounts
            ],
            'vfolder_mounts': vfolder_mounts,
            'repl_in_port': 0,
            'repl_out_port': 0,
            'stdin_port': 0,
            'stdout_port': 0,
        }
        kernel_data = []

        for idx, kernel in enumerate(kernel_enqueue_configs):
            kernel_id = KernelId(uuid.uuid4())
            creation_config = kernel['creation_config']
            resource_opts = creation_config.get('resource_opts') or {}

            image_ref = kernel['image_ref']
            image_row = image_map[image_ref.canonical]
            image_min_slots, image_max_slots = await image_row.get_slot_ranges(self.shared_config)
            known_slot_types = await self.shared_config.get_resource_slots()

            labels = image_row.labels
            # Parse service ports to check for port errors
            parse_service_ports(labels.get('ai.backend.service-ports', ''), BackendError)

            # Shared memory.
            # We need to subtract the amount of shared memory from the memory limit of
            # a container, since tmpfs including /dev/shm uses host-side kernel memory
            # and cgroup's memory limit does not apply.
            shmem = resource_opts.get('shmem', None)
            if shmem is None:
                shmem = labels.get('ai.backend.resource.preferred.shmem', '64m')
            shmem = BinarySize.from_str(shmem)
            resource_opts['shmem'] = shmem
            image_min_slots = copy.deepcopy(image_min_slots)
            image_min_slots['mem'] += shmem

            # Sanitize user input: does it have resource config?
            if 'resources' in creation_config:
                # Sanitize user input: does it have "known" resource slots only?
                for slot_key, slot_value in creation_config['resources'].items():
                    if slot_key not in known_slot_types:
                        raise InvalidAPIParameters(
                            f'Unknown requested resource slot: {slot_key}')
                try:
                    requested_slots = ResourceSlot.from_user_input(
                        creation_config['resources'], known_slot_types)
                except ValueError:
                    log.exception('request_slots & image_slots calculation error')
                    # happens when requested_slots have more keys
                    # than the image-defined slots
                    # (e.g., image does not support accelerators
                    #  requested by the client)
                    raise InvalidAPIParameters(
                        'Your resource request has resource type(s) '
                        'not supported by the image.')

                # If intrinsic resources are not specified,
                # fill them with image minimums.
                for k, v in requested_slots.items():
                    if (v is None or v == 0) and k in INTRINSIC_SLOTS:
                        requested_slots[k] = image_min_slots[k]
            else:
                # Handle the legacy clients (prior to v19.03)
                # We support CPU/memory conversion, but to use accelerators users
                # must update their clients because the slots names are not provided
                # by the accelerator plugins.
                cpu = creation_config.get('instanceCores')
                if cpu is None:  # the key is there but may be null.
                    cpu = image_min_slots['cpu']
                mem = creation_config.get('instanceMemory')
                if mem is None:  # the key is there but may be null.
                    mem = image_min_slots['mem']
                else:
                    # In legacy clients, memory is normalized to GiB.
                    mem = str(mem) + 'g'
                requested_slots = ResourceSlot.from_user_input({
                    'cpu': cpu,
                    'mem': mem,
                }, known_slot_types)
                gpu = creation_config.get('instanceGPUs')
                if gpu is not None:
                    raise InvalidAPIParameters('Client upgrade required '
                                               'to use GPUs (v19.03+).')
                tpu = creation_config.get('instanceTPUs')
                if tpu is not None:
                    raise InvalidAPIParameters('Client upgrade required '
                                               'to use TPUs (v19.03+).')

            # Check the image resource slots.
            log_fmt = "s:{} k:{} r:{}-{}"
            log_args = (session_id, kernel_id, kernel['cluster_role'], kernel['cluster_idx'])
            log.debug(log_fmt + ' -> requested_slots: {}', *log_args, requested_slots)
            log.debug(log_fmt + ' -> resource_opts: {}', *log_args, resource_opts)
            log.debug(log_fmt + ' -> image_min_slots: {}', *log_args, image_min_slots)
            log.debug(log_fmt + ' -> image_max_slots: {}', *log_args, image_max_slots)

            # Check if: requested >= image-minimum
            if image_min_slots > requested_slots:
                raise InvalidAPIParameters(
                    'Your resource request is smaller than '
                    'the minimum required by the image. ({})'.format(' '.join(
                        f'{k}={v}' for k, v in
                        image_min_slots.to_humanized(known_slot_types).items()
                    )))

            # Check if: requested <= image-maximum
            if not (requested_slots <= image_max_slots):
                raise InvalidAPIParameters(
                    'Your resource request is larger than '
                    'the maximum allowed by the image. ({})'
                    .format(' '.join(
                        f'{k}={v}' for k, v in
                        image_max_slots.to_humanized(known_slot_types).items()
                    )))

            # Check if: shmem < memory
            if shmem >= requested_slots['mem']:
                raise InvalidAPIParameters(
                    'Shared memory should be less than the main memory. (s:{}, m:{})'
                    .format(str(shmem), str(BinarySize(requested_slots['mem']))),
                )

            # Add requested resource slot data to session
            session_data['requested_slots'] += requested_slots

            environ = session_creation_config.get('environ') or {}

            # Create kernel object in PENDING state.
            mapped_agent = None
            if not agent_list:
                pass
            else:
                mapped_agent = agent_list[idx]

            kernel_data.append({
                **kernel_shared_data,
                'id': kernel_id,
                'agent_id': mapped_agent,
                'cluster_role': kernel['cluster_role'],
                'cluster_idx': kernel['cluster_idx'],
                'cluster_hostname': f"{kernel['cluster_role']}{kernel['cluster_idx']}"
                if not kernel['cluster_hostname'] else kernel['cluster_hostname'],
                'image_id': image_row.id,
                'architecture': image_ref.architecture,
                'registry': image_ref.registry,
                'startup_command': kernel.get('startup_command'),
                'occupied_slots': ResourceSlot(),
                'requested_slots': requested_slots,
                'resource_opts': resource_opts,
                'environ': [f'{k}={v}' for k, v in environ.items()],
                'bootstrap_script': kernel.get('bootstrap_script'),
                'preopen_ports': creation_config.get('preopen_ports', []),
            })

        try:
            async def _enqueue() -> None:
                async with self.db.begin_session() as db_sess:
                    try:
                        await enqueue_session(
                            db_sess, access_key,
                            session_data, kernel_data,
                            dependency_sessions,
                        )
                    except UnknownDependencySession as e:
                        raise InvalidAPIParameters(
                            "Unknown session ID or name in the dependency list",
                            extra_data={"session_ref": e},
                        )

            await execute_with_retry(_enqueue)
        except DBAPIError as e:
            if getattr(e.orig, "pgcode", None) == '23503':
                match = re.search(r'Key \(agent\)=\((?P<agent>[^)]+)\)', repr(e.orig))
                if match:
                    raise InvalidAPIParameters(f"No such agent: {match.group('agent')}")
                else:
                    raise InvalidAPIParameters("No such agent")
            raise

        await self.hook_plugin_ctx.notify(
            'POST_ENQUEUE_SESSION',
            (session_id, session_name, access_key),
        )
        await self.event_producer.produce_event(
            SessionEnqueuedEvent(session_id, session_creation_id),
        )
        return session_id

    async def start_session(
        self,
        sched_ctx: SchedulingContext,
        scheduled_session: SessionRow,
    ) -> None:
        from .scheduler.types import KernelAgentBinding
        kernel_agent_bindings: Sequence[KernelAgentBinding] = [
            KernelAgentBinding(
                kernel=k,
                agent_alloc_ctx=k.agent,
            )
            for k in scheduled_session.kernels
        ]
        session_id, session_creation_id = scheduled_session.id, scheduled_session.creation_id

        hook_result = await self.hook_plugin_ctx.dispatch(
            'PRE_START_SESSION',
            (session_id, scheduled_session.name, scheduled_session.kp_access_key),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)

        # Get resource policy for the session
        # TODO: memoize with TTL
        # async with self.db.begin_readonly_session() as sess:
        #     query = (
        #         sa.select([keypair_resource_policies])
        #         .select_from(keypair_resource_policies)
        #         .where(keypair_resource_policies.c.name == scheduled_session.resource_policy)
        #     )
        #     result = await sess.execute(query)
        #     resource_policy = result.first()
        resource_policy = scheduled_session.access_key.resource_policy
        auto_pull = await self.shared_config.get_raw('config/docker/image/auto_pull')

        # Aggregate image registry information
        image_infos = {}
        async with self.db.begin_readonly_session() as session:
            for image_row, _ in itertools.groupby(
                sorted(kernel_agent_bindings, key=lambda item: item.kernel.image_id),
                key=lambda item: item.kernel.image,
            ):
                image_ref = image_row.image_ref
                log.debug('start_session(): image ref => {} ({})', image_ref, image_ref.architecture)
                image_infos[image_ref] = await ImageRow.resolve(session, [image_ref])
                registry_url, registry_creds = \
                    await get_registry_info(self.shared_config.etcd, image_ref.registry)
        image_info = {
            'image_infos': image_infos,
            'registry_url': registry_url,
            'registry_creds': registry_creds,
            'resource_policy': resource_policy,
            'auto_pull': auto_pull,
        }

        network_name: Optional[str] = None
        if scheduled_session.cluster_mode == ClusterMode.SINGLE_NODE:
            if scheduled_session.cluster_size > 1:
                network_name = f'bai-singlenode-{session_id}'
                assert kernel_agent_bindings[0].agent_alloc_ctx.id is not None
                assert session_id is not None
                try:
                    async with RPCContext(
                        kernel_agent_bindings[0].agent_alloc_ctx.id,
                        kernel_agent_bindings[0].agent_alloc_ctx.addr,
                        invoke_timeout=None,
                        order_key=str(session_id),
                        keepalive_timeout=self.rpc_keepalive_timeout,
                    ) as rpc:
                        await rpc.call.create_local_network(network_name)
                except Exception:
                    log.exception(f"Failed to create an agent-local network {network_name}")
                    raise
            else:
                network_name = None
        elif scheduled_session.cluster_mode == ClusterMode.MULTI_NODE:
            # Create overlay network for multi-node sessions
            network_name = f'bai-multinode-{session_id}'
            mtu = await self.shared_config.get_raw('config/network/overlay/mtu')
            try:
                # Overlay networks can only be created at the Swarm manager.
                create_options = {
                    'Name': network_name,
                    'Driver': 'overlay',
                    'Attachable': True,
                    'Labels': {
                        'ai.backend.cluster-network': '1',
                    },
                    'Options': {},
                }
                if mtu:
                    create_options['Options'] = {'com.docker.network.driver.mtu': mtu}
                await self.docker.networks.create(create_options)
            except Exception:
                log.exception(f"Failed to create an overlay network {network_name}")
                raise
        keyfunc = lambda item: item.kernel.cluster_role
        replicas = {
            cluster_role: len([*group_iterator])
            for cluster_role, group_iterator in itertools.groupby(
                sorted(kernel_agent_bindings, key=keyfunc),
                key=keyfunc,
            )
        }
        cluster_info = ClusterInfo(
            mode=scheduled_session.cluster_mode,
            size=scheduled_session.cluster_size,
            replicas=replicas,
            network_name=network_name,
            ssh_keypair=(
                await self.create_cluster_ssh_keypair()
                if scheduled_session.cluster_size > 1 else None
            ),
        )
        sess_env = scheduled_session.environ
        scheduled_session.environ = {
            **sess_env,
            'BACKENDAI_SESSION_ID': str(session_id),
            'BACKENDAI_SESSION_NAME': str(scheduled_session.name),
            'BACKENDAI_CLUSTER_SIZE': str(scheduled_session.cluster_size),
            'BACKENDAI_CLUSTER_REPLICAS':
                ",".join(f"{k}:{v}" for k, v in replicas.items()),
            'BACKENDAI_CLUSTER_HOSTS':
                ",".join(binding.kernel.cluster_hostname for binding in kernel_agent_bindings),
            'BACKENDAI_ACCESS_KEY': scheduled_session.kp_access_key,
        }

        # Aggregate by agents to minimize RPC calls
        per_agent_tasks = []
        keyfunc = lambda item: item.agent_alloc_ctx.id
        for agent_id, group_iterator in itertools.groupby(
            sorted(kernel_agent_bindings, key=keyfunc), key=keyfunc,
        ):
            items = [*group_iterator]
            # Within a group, agent_alloc_ctx are same.
            agent_alloc_ctx = items[0].agent_alloc_ctx
            per_agent_tasks.append(
                (
                    agent_alloc_ctx,
                    self._create_kernels_in_one_agent(
                        agent_alloc_ctx,
                        scheduled_session,
                        items,
                        image_info,
                        cluster_info,
                    ),
                ),
            )
        if per_agent_tasks:
            agent_errors = []
            results = await asyncio.gather(
                *[item[1] for item in per_agent_tasks],
                return_exceptions=True,
            )
            for agent_alloc_tx, result in zip((item[0] for item in per_agent_tasks), results):
                if isinstance(result, aiotools.TaskGroupError):
                    agent_errors.extend(result.__errors__)
                elif isinstance(result, Exception):
                    # mark to be destroyed afterwards
                    agent_errors.append(result)
            if agent_errors:
                raise MultiAgentError(
                    "agent(s) raise errors during kernel creation",
                    errors=agent_errors,
                )
            await self.settle_agent_alloc(kernel_agent_bindings)

        async with self.db.begin_session() as db_session:
            total_resource_occupancy = await get_kernel_occupancy(
                db_session,
                (KernelRow.session_id == session_id),
                status_choice=None,
            )
            query = (
                sa.update(SessionRow)
                .values(
                    occupying_slots=total_resource_occupancy,
                    status=SessionStatus.RUNNING,
                    status_changed=datetime.now(tzutc()),
                )
                .where(SessionRow.id == session_id)
            )
            await db_session.execute(query)
        # If all is well, let's say the session is ready.
        await self.event_producer.produce_event(
            SessionStartedEvent(session_id, session_creation_id),
        )
        await self.hook_plugin_ctx.notify(
            'POST_START_SESSION',
            (session_id, scheduled_session.name, scheduled_session.kp_access_key),
        )

    def convert_resource_spec_to_resource_slot(
        self,
        allocations: Mapping[str, Mapping[SlotName, Mapping[DeviceId, str]]],
    ) -> ResourceSlot:
        """
        Convert per-device resource spec allocations (agent-side format)
        back into a resource slot (manager-side format).
        """
        slots = ResourceSlot()
        for alloc_map in allocations.values():
            for slot_name, allocation_by_device in alloc_map.items():
                total_allocs: List[Decimal] = []
                for allocation in allocation_by_device.values():
                    if BinarySize.suffix_map.get(allocation[-1].lower()) is not None:
                        total_allocs.append(Decimal(BinarySize.from_str(allocation)))
                    else:
                        total_allocs.append(Decimal(allocation))
                slots[slot_name] = str(sum(total_allocs))
        return slots

    async def _post_create_kernel(
        self,
        agent_alloc_ctx: AgentRow,
        kernel_id: KernelId,
    ) -> None:
        # Wait until the kernel_started event.
        try:
            created_info, _ = await asyncio.gather(
                self._post_kernel_creation_infos[kernel_id],
                self.kernel_creation_tracker[kernel_id],
            )
        except asyncio.CancelledError:
            log.warning("post_create_kernel(k:{}) cancelled", kernel_id)
            return
        except Exception:
            log.exception("post_create_kernel(k:{}) unexpected error", kernel_id)
            return
        else:

            async def _finialize_running() -> None:
                # Record kernel access information
                try:
                    async with self.db.begin_session() as db_sess:
                        agent_host = URL(agent_alloc_ctx.addr).host
                        kernel_host = created_info.get('kernel_host', agent_host)
                        service_ports = created_info.get('service_ports', [])
                        # NOTE: created_info contains resource_spec
                        values = {
                            'scaling_group': agent_alloc_ctx.scaling_group_name,
                            'status': KernelStatus.RUNNING,
                            'status_changed': datetime.now(tzutc()),
                            'container_id': created_info['container_id'],
                            'occupied_shares': {},
                            'attached_devices': created_info.get('attached_devices', {}),
                            'kernel_host': kernel_host,
                            'repl_in_port': created_info['repl_in_port'],
                            'repl_out_port': created_info['repl_out_port'],
                            'stdin_port': created_info['stdin_port'],
                            'stdout_port': created_info['stdout_port'],
                            'service_ports': service_ports,
                        }
                        actual_allocs = self.convert_resource_spec_to_resource_slot(
                            created_info['resource_spec']['allocations'])
                        values['occupied_slots'] = actual_allocs
                        self._kernel_actual_allocated_resources[kernel_id] = actual_allocs

                        update_query = (
                            sa.update(KernelRow)
                            .values(**values)
                            .where(KernelRow.id == created_info['id'])
                        )
                        await db_sess.execute(update_query)
                except Exception:
                    log.exception('error while executing _finalize_running')
                    raise
            await execute_with_retry(_finialize_running)
        finally:
            try:
                await asyncio.sleep(1)
            finally:
                del self._post_kernel_creation_infos[kernel_id]
                del self.kernel_creation_tracker[kernel_id]

    async def _create_kernels_in_one_agent(
        self,
        agent_alloc_ctx: AgentRow,
        scheduled_session: SessionRow,
        items: Sequence[KernelAgentBinding],
        image_info,
        cluster_info,
    ) -> None:
        loop = asyncio.get_running_loop()
        registry_url = image_info['registry_url']
        registry_creds = image_info['registry_creds']
        image_infos = image_info['image_infos']
        resource_policy = image_info['resource_policy']
        auto_pull = image_info['auto_pull']
        assert agent_alloc_ctx.id is not None
        assert scheduled_session.id is not None
        async with RPCContext(
            agent_alloc_ctx.id,
            agent_alloc_ctx.addr,
            invoke_timeout=None,
            order_key=str(scheduled_session.id),
            keepalive_timeout=self.rpc_keepalive_timeout,
        ) as rpc:
            kernel_creation_id = secrets.token_urlsafe(16)
            # Prepare kernel_started event handling
            for binding in items:
                self.kernel_creation_tracker[
                    binding.kernel.id
                ] = loop.create_future()
            # Spawn post-processing tasks
            post_tasks = []
            for binding in items:
                self._post_kernel_creation_infos[binding.kernel.id] = loop.create_future()
                post_task = asyncio.create_task(self._post_create_kernel(
                    agent_alloc_ctx,
                    binding.kernel.id,
                ))
                self._post_kernel_creation_tasks[binding.kernel.id] = post_task
                post_tasks.append(post_task)
            try:
                # Issue a batched RPC call to create kernels on this agent
                created_infos = await rpc.call.create_kernels(
                    kernel_creation_id,
                    str(scheduled_session.id),
                    [str(binding.kernel.id) for binding in items],
                    [
                        {
                            'image': {
                                'registry': {
                                    'name': binding.kernel.image.image_ref.registry,
                                    'url': str(registry_url),
                                    **registry_creds,   # type: ignore
                                },
                                'digest': image_infos[binding.kernel.image.image_ref].config_digest,
                                'repo_digest': None,
                                'canonical': binding.kernel.image.image_ref.canonical,
                                'architecture': binding.kernel.image.image_ref.architecture,
                                'labels': image_infos[binding.kernel.image.image_ref].labels,
                            },
                            'session_type': scheduled_session.session_type.value,
                            'cluster_role': binding.kernel.cluster_role,
                            'cluster_idx': binding.kernel.cluster_idx,
                            'cluster_hostname': binding.kernel.cluster_hostname,
                            'idle_timeout': resource_policy.idle_timeout,
                            'mounts': [item.to_json() for item in scheduled_session.vfolder_mounts],
                            'environ': {
                                # inherit per-session environment variables
                                **scheduled_session.environ,
                                # set per-kernel environment variables
                                'BACKENDAI_KERNEL_ID': str(binding.kernel.id),
                                'BACKENDAI_KERNEL_IMAGE': str(binding.kernel.image.image_ref),
                                'BACKENDAI_CLUSTER_ROLE': binding.kernel.cluster_role,
                                'BACKENDAI_CLUSTER_IDX': str(binding.kernel.cluster_idx),
                                'BACKENDAI_CLUSTER_HOST': str(binding.kernel.cluster_hostname),
                            },
                            'resource_slots': binding.kernel.requested_slots.to_json(),
                            'resource_opts': binding.kernel.resource_opts,
                            'bootstrap_script': binding.kernel.bootstrap_script,
                            'startup_command': binding.kernel.startup_command,
                            'internal_data': scheduled_session.main_kernel.internal_data,
                            'auto_pull': auto_pull,
                            'preopen_ports': scheduled_session.main_kernel.preopen_ports,
                        }
                        for binding in items
                    ],
                    cluster_info,
                )
                log.debug(
                    'start_session(s:{}, ak:{}, k:{}) -> created on ag:{}',
                    scheduled_session.name,
                    scheduled_session.kp_access_key,
                    [binding.kernel.id for binding in items],
                    agent_alloc_ctx.id,
                )
                # Pass the return value of RPC calls to post-processing tasks
                for created_info in created_infos:
                    kernel_id = KernelId(uuid.UUID(created_info['id']))
                    self._post_kernel_creation_infos[kernel_id].set_result(created_info)
                await asyncio.gather(*post_tasks, return_exceptions=True)
            except Exception as e:
                # The agent has already cancelled or issued the destruction lifecycle event
                # for this batch of kernels.
                for binding in items:
                    kernel_id = binding.kernel.id
                    self.kernel_creation_tracker[kernel_id].cancel()
                    self._post_kernel_creation_infos[kernel_id].set_exception(e)
                await asyncio.gather(*post_tasks, return_exceptions=True)
                raise

    async def create_cluster_ssh_keypair(self) -> ClusterSSHKeyPair:
        key = rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=2048,
        )
        public_key = key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH,
        )
        public_key += b' work@cluster.backend.ai.local'
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return {
            'private_key': pem.decode('utf-8'),
            'public_key': public_key.decode('utf-8'),
        }

    async def get_keypair_occupancy(self, access_key, *, sess=None):
        known_slot_types = \
            await self.shared_config.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn(self.db, sess) as _sess:
                return await get_kernel_occupancy(
                    _sess,
                    cond=(KernelRow.access_key == access_key),
                    slot_filter=known_slot_types,
                )

        return await execute_with_retry(_query)

    async def get_domain_occupancy(self, domain_name, *, sess=None):
        # TODO: store domain occupied_slots in Redis?
        known_slot_types = await self.shared_config.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn(self.db, sess) as _sess:
                return await get_kernel_occupancy(
                    _sess,
                    cond=(KernelRow.domain_name == domain_name),
                    slot_filter=known_slot_types,
                )

        return await execute_with_retry(_query)

    async def get_group_occupancy(self, group_id, *, sess=None):
        # TODO: store domain occupied_slots in Redis?
        known_slot_types = await self.shared_config.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, sess) as _sess:
                return await get_kernel_occupancy(
                    _sess,
                    cond=(KernelRow.group_id == group_id),
                    slot_filter=known_slot_types,
                )

        return await execute_with_retry(_query)

    async def update_scaling_group(self, id, scaling_group) -> None:
        agent = await self.get_instance(id, agents.c.addr)
        async with RPCContext(
            agent['id'],
            agent['addr'],
            invoke_timeout=None,
            keepalive_timeout=self.rpc_keepalive_timeout,
        ) as rpc:
            await rpc.call.update_scaling_group(scaling_group)

    async def settle_agent_alloc(
        self, kernel_agent_bindings: Sequence[KernelAgentBinding],
    ) -> None:
        """
        Tries to settle down agent row's occupied_slots with real value. This must be called
        after kernel creation is completed, to prevent fraction of resource dropped by agent scheduler
        during kernel creation still being reported as used.
        """

        keyfunc = lambda item: item.agent_alloc_ctx.id
        for agent_id, group_iterator in itertools.groupby(
            sorted(kernel_agent_bindings, key=keyfunc), key=keyfunc,
        ):
            actual_allocated_slots = ResourceSlot()
            requested_slots = ResourceSlot()

            for kernel_agent_binding in group_iterator:
                # this value must be set while running _post_create_kernel
                actual_allocated_slot = self._kernel_actual_allocated_resources.get(
                    kernel_agent_binding.kernel.id)
                requested_slots += kernel_agent_binding.kernel.requested_slots
                if actual_allocated_slot is not None:
                    actual_allocated_slots += ResourceSlot.from_json(actual_allocated_slot)
                    del self._kernel_actual_allocated_resources[kernel_agent_binding.kernel.id]
                else:  # something's wrong; just fall back to requested slot value
                    actual_allocated_slots += kernel_agent_binding.kernel.requested_slots

            # perform DB update only if requested slots and actual allocated value differs
            if actual_allocated_slots != requested_slots:
                log.debug('calibrating resource slot usage for agent {}', agent_id)
                async with self.db.begin_session() as db_sess:
                    select_query = (
                        sa.select(AgentRow.occupied_slots)
                        .where(AgentRow.id == agent_id)
                    )
                    result = await db_sess.execute(select_query)
                    occupied_slots: ResourceSlot = result.scalar()

                    diff = actual_allocated_slots - requested_slots
                    update_query = (
                        sa.update(AgentRow)
                        .values(
                            occupied_slots=ResourceSlot.from_json(occupied_slots) + diff,
                        )
                        .where(AgentRow.id == agent_id)
                    )
                    await db_sess.execute(update_query)

    async def recalc_resource_usage(self, do_fullscan: bool = False) -> None:
        concurrency_used_per_key: MutableMapping[str, int] = defaultdict(lambda: 0)
        occupied_slots_per_agent: MutableMapping[str, ResourceSlot] = \
            defaultdict(lambda: ResourceSlot({'cpu': 0, 'mem': 0}))

        async def _recalc() -> None:
            async with self.db.begin_session() as db_sess:
                # Query running containers and calculate concurrency_used per AK and
                # occupied_slots per agent.
                all_filtering_statues = (
                    set(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES) |
                    set(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES)
                )
                query = (
                    sa.select(
                        KernelRow.access_key,
                        KernelRow.agent_id,
                        KernelRow.occupied_slots,
                        KernelRow.status,
                    )
                    .where(KernelRow.status.in_(all_filtering_statues))
                    .order_by(sa.asc(KernelRow.access_key))
                )
                async for row in (await db_sess.stream(query)):
                    if row.status in AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES:
                        occupied_slots_per_agent[row.agent_id] += ResourceSlot(row.occupied_slots)
                    if row.status in USER_RESOURCE_OCCUPYING_KERNEL_STATUSES:
                        concurrency_used_per_key[row.access_key] += 1
                # query = (
                #     sa.select([kernels.c.access_key, kernels.c.agent_id, kernels.c.occupied_slots])
                #     .where(kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                #     .order_by(sa.asc(kernels.c.access_key))
                # )
                # async for row in (await conn.stream(query)):
                #     occupied_slots_per_agent[row.agent_id] += ResourceSlot(row.occupied_slots)
                # query = (
                #     sa.select([kernels.c.access_key, kernels.c.agent_id, kernels.c.occupied_slots])
                #     .where(kernels.c.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                #     .order_by(sa.asc(kernels.c.access_key))
                # )
                # async for row in (await conn.stream(query)):
                #     concurrency_used_per_key[row.access_key] += 1

                if len(occupied_slots_per_agent) > 0:
                    # Update occupied_slots for agents with running containers.
                    for aid, slots in occupied_slots_per_agent.items():
                        query = (
                            sa.update(AgentRow)
                            .values(occupied_slots=slots)
                            .where(AgentRow.id == aid)
                        )
                        await db_sess.execute(query)
                    # Update all other agents to have empty occupied_slots.
                    query = (
                        sa.update(AgentRow)
                        .values(occupied_slots=ResourceSlot({}))
                        .where(AgentRow.status == AgentStatus.ALIVE)
                        .where(sa.not_(AgentRow.id.in_(occupied_slots_per_agent.keys())))
                    )
                    await db_sess.execute(query)
                else:
                    query = (
                        sa.update(AgentRow)
                        .values(occupied_slots=ResourceSlot({}))
                        .where(AgentRow.status == AgentStatus.ALIVE)
                    )
                    await db_sess.execute(query)

        await execute_with_retry(_recalc)

        # Update keypair resource usage for keypairs with running containers.
        kp_key = 'keypair.concurrency_used'

        async def _update(r: aioredis.Redis):
            updates: Mapping[str, int] = \
                {f'{kp_key}.{k}': concurrency_used_per_key[k] for k in concurrency_used_per_key}
            if updates:
                await r.mset(updates)

        async def _update_by_fullscan(r: aioredis.Redis):
            updates: Dict[str, int] = {}
            keys = await r.keys(f'{kp_key}.*')
            for ak in keys:
                usage = concurrency_used_per_key.get(ak, 0)
                updates[f'{kp_key}.{ak}'] = usage
            if updates:
                await r.mset(updates)

        if do_fullscan:
            await redis.execute(
                self.redis_stat,
                _update_by_fullscan,
            )
        else:
            await redis.execute(
                self.redis_stat,
                _update,
            )

    async def destroy_session_lowlevel(
        self,
        session_id: SessionId,
        kernels: Sequence[Mapping],  # should have (id, agent, agent_addr, container_id) columns
    ) -> None:
        """
        Destroy the kernels that belongs the to given session unconditionally
        and without generation of any relevant events nor invocation of plugin hooks.
        """
        keyfunc = lambda item: item['agent'] if item['agent'] is not None else ''
        for agent_id, group_iterator in itertools.groupby(
            sorted(kernels, key=keyfunc), key=keyfunc,
        ):
            rpc_coros = []
            destroyed_kernels = []
            grouped_kernels = [*group_iterator]
            for kernel in grouped_kernels:
                if kernel['container_id'] is not None and kernel['agent_addr'] is not None:
                    destroyed_kernels.append(kernel)
            if not destroyed_kernels:
                return
            async with RPCContext(
                destroyed_kernels[0]['agent'],
                destroyed_kernels[0]['agent_addr'],
                invoke_timeout=None,
                order_key=str(session_id),
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                for kernel in destroyed_kernels:
                    # internally it enqueues a "destroy" lifecycle event.
                    rpc_coros.append(
                        rpc.call.destroy_kernel(
                            str(kernel['id']),
                            "failed-to-start",
                            suppress_events=True,
                        ),
                    )
                await asyncio.gather(*rpc_coros)

    async def destroy_session(
        self,
        session_getter: SessionGetter,
        *,
        forced: bool = False,
        reason: str = 'user-requested',
    ) -> Mapping[str, Any]:
        """
        Destroy session kernels. Do not destroy
        PREPARING/TERMINATING/ERROR and PULLING sessions.

        :param forced: If True, destroy PREPARING/TERMINATING/ERROR session.
                       However, PULLING session still cannot be destroyed.
        :param reason: Reason to destroy a session if client wants to specify it manually.
        """
        async with self.db.begin_readonly_session() as db_sess:
            session: SessionRow
            session = await session_getter(
                db_session=db_sess,
                load_kernels=True,
            )
        if forced:
            reason = 'force-terminated'
        hook_result = await self.hook_plugin_ctx.dispatch(
            'PRE_DESTROY_SESSION',
            (session.id, session.name, session.kp_access_key),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)

        kernel_list: Sequence[KernelRow] = session.kernels
        main_stat = {}
        per_agent_tasks = []
        now = datetime.now(tzutc())

        keyfunc = lambda item: item.agent if item.agent is not None else ''
        for agent_id, group_iterator in itertools.groupby(
            sorted(kernel_list, key=keyfunc), key=keyfunc,
        ):
            destroyed_kernels = []
            grouped_kernels = [*group_iterator]
            kernel: KernelRow
            kernel_statues: List[KernelStatus] = []
            for kernel in grouped_kernels:
                async with self.handle_kernel_exception(
                    'destroy_session', kernel.id, session.kp_access_key, set_error=True,
                ):
                    if kernel.status == KernelStatus.PENDING:
                        transit_to = KernelStatus.CANCELLED

                        async def _update() -> None:
                            values = {
                                'status': transit_to,
                                'status_info': reason,
                                'status_changed': now,
                                'terminated_at': now,
                            }
                            async with self.db.begin_session() as db_sess:
                                query = (
                                    sa.update(KernelRow)
                                    .values(**values)
                                    .where(KernelRow.id == kernel.id)
                                )
                                await db_sess.execute(query)

                        await execute_with_retry(_update)
                        await self.event_producer.produce_event(
                            KernelCancelledEvent(kernel.id, '', reason),
                        )
                        if kernel.cluster_role == DEFAULT_ROLE:
                            main_stat = {'status': 'cancelled'}
                            await self.event_producer.produce_event(
                                SessionCancelledEvent(
                                    kernel.session_id,
                                    session.creation_id,
                                    reason,
                                ),
                            )
                    elif kernel.status == KernelStatus.PULLING:
                        raise GenericForbidden('Cannot destroy kernels in pulling status')
                    elif kernel.status in (
                        KernelStatus.SCHEDULED,
                        KernelStatus.PREPARING,
                        KernelStatus.TERMINATING,
                        KernelStatus.ERROR,
                    ):
                        if not forced:
                            raise GenericForbidden(
                                'Cannot destroy kernels in scheduled/preparing/terminating/error status',
                            )
                        log.warning('force-terminating kernel (k:{}, status:{})',
                                    kernel.id, kernel.status)
                        if kernel.container_id is not None:
                            destroyed_kernels.append(kernel)

                        if kernel.cluster_role == DEFAULT_ROLE:
                            # The main session is terminated;
                            # decrement the user's concurrency counter
                            await redis.execute(
                                self.redis_stat,
                                lambda r: r.incrby(
                                    f"keypair.concurrency_used.{kernel.access_key}",
                                    -1,
                                ),
                            )

                        transit_to = KernelStatus.TERMINATED

                        async def _update() -> None:
                            kern_stat = await redis.execute(
                                self.redis_stat,
                                lambda r: r.get(str(kernel.id)),
                            )
                            values = {
                                'status': transit_to,
                                'status_info': reason,
                                'status_changed': now,
                                'terminated_at': now,
                            }
                            if kern_stat:
                                values['last_stat'] = msgpack.unpackb(kern_stat)
                            async with self.db.begin_session() as db_sess:
                                query = (
                                    sa.update(KernelRow)
                                    .values(**values)
                                    .where(KernelRow.id == kernel.id)
                                )
                                await db_sess.execute(query)

                        await execute_with_retry(_update)
                        await self.event_producer.produce_event(
                            KernelTerminatedEvent(kernel.id, reason),
                        )
                    else:

                        if kernel.cluster_role == DEFAULT_ROLE:
                            # The main session is terminated;
                            # decrement the user's concurrency counter
                            await redis.execute(
                                self.redis_stat,
                                lambda r: r.incrby(
                                    f"keypair.concurrency_used.{kernel.access_key}",
                                    -1,
                                ),
                            )

                        transit_to = KernelStatus.TERMINATING

                        async def _update() -> None:
                            value = {
                                'status': KernelStatus.TERMINATING,
                                'status_info': reason,
                                'status_changed': now,
                                'status_data': {
                                    "kernel": {"exit_code": None},
                                    "session": {"status": "terminating"},
                                },
                            }
                            async with self.db.begin_session() as db_sess:
                                query = (
                                    sa.update(KernelRow)
                                    .values(**value)
                                    .where(KernelRow.id == kernel.id)
                                )
                                await db_sess.execute(query)

                        await execute_with_retry(_update)
                        await self.event_producer.produce_event(
                            KernelTerminatingEvent(kernel.id, reason),
                        )
                    kernel_statues.append(transit_to)

                    if kernel.agent_addr is None:
                        await self.mark_kernel_terminated(kernel.id, 'missing-agent-allocation')
                        if kernel.cluster_role == DEFAULT_ROLE:
                            main_stat = {'status': 'terminated'}
                    else:
                        destroyed_kernels.append(kernel)

                async def _destroy_kernels_in_agent(session, destroyed_kernels) -> None:
                    nonlocal main_stat
                    async with RPCContext(
                        destroyed_kernels[0]['agent'],
                        destroyed_kernels[0]['agent_addr'],
                        invoke_timeout=None,
                        order_key=session.id,
                        keepalive_timeout=self.rpc_keepalive_timeout,
                    ) as rpc:
                        rpc_coros = []
                        for kernel in destroyed_kernels:
                            # internally it enqueues a "destroy" lifecycle event.
                            if kernel.status != KernelStatus.SCHEDULED:
                                rpc_coros.append(
                                    rpc.call.destroy_kernel(str(kernel.id), reason),
                                )
                        try:
                            await asyncio.gather(*rpc_coros)
                        except Exception:
                            log.exception(
                                "destroy_kernels_in_agent(a:{}, s:{}): unexpected error",
                                destroyed_kernels[0]['agent'],
                                session.id,
                            )
                        for kernel in destroyed_kernels:
                            last_stat: Optional[Dict[str, Any]]
                            last_stat = None
                            try:
                                raw_last_stat = await redis.execute(
                                    self.redis_stat,
                                    lambda r: r.get(str(kernel.id)))
                                if raw_last_stat is not None:
                                    last_stat = msgpack.unpackb(raw_last_stat)
                                    last_stat['version'] = 2
                            except asyncio.TimeoutError:
                                pass
                            if kernel.cluster_role == DEFAULT_ROLE:
                                main_stat = {
                                    **(last_stat if last_stat is not None else {}),
                                    'status': 'terminated',
                                }

                if destroyed_kernels:
                    per_agent_tasks.append(_destroy_kernels_in_agent(session, destroyed_kernels))

            if per_agent_tasks:
                await asyncio.gather(*per_agent_tasks, return_exceptions=True)
            if forced:
                await self.recalc_resource_usage()
            sess_status = aggregate_kernel_status(kernel_statues)
        values = {
            'status': sess_status,
            'status_info': reason,
            'status_changed': now,
            'terminated_at': now,
        }
        async with self.db.begin_session() as db_sess:
            query = (
                sa.update(SessionRow)
                .values(**values)
                .where(SessionRow.id == session.id)
            )
            await db_sess.execute(query)
        await self.hook_plugin_ctx.notify(
            'POST_DESTROY_SESSION',
            (session.id, session.name, session.kp_access_key),
        )
        return main_stat

    async def clean_session(
        self,
        session_id: SessionId,
    ) -> None:

        async def _fetch() -> Row:
            async with self.db.begin_readonly_session() as db_sess:
                query = (
                    sa.select(
                        KernelRow.session_id,
                        KernelRow.cluster_mode,
                        KernelRow.cluster_size,
                        KernelRow.agent_id,
                        KernelRow.agent_addr,
                    )
                    .where(
                        (KernelRow.session_id == session_id) &
                        (KernelRow.cluster_role == DEFAULT_ROLE),
                    )
                )
                result = await db_sess.execute(query)
                return result.first()

        session = dict(await execute_with_retry(_fetch))
        if session is None:
            return
        if session['cluster_mode'] == ClusterMode.SINGLE_NODE and session['cluster_size'] > 1:
            network_name = f'bai-singlenode-{session["session_id"]}'
            try:
                async with RPCContext(
                    session['agent'],       # the main-container's agent
                    session['agent_addr'],
                    invoke_timeout=None,
                    order_key=session['session_id'],
                    keepalive_timeout=self.rpc_keepalive_timeout,
                ) as rpc:
                    await rpc.call.destroy_local_network(network_name)
            except Exception:
                log.exception(f"Failed to destroy the agent-local network {network_name}")
        elif session['cluster_mode'] == ClusterMode.MULTI_NODE:
            network_name = f'bai-multinode-{session["session_id"]}'
            try:
                try:
                    # await rpc.call.destroy_overlay_network(network_name)
                    await asyncio.sleep(2.0)
                    network = await self.docker.networks.get(network_name)
                    await network.delete()
                except aiodocker.DockerError as e:
                    if e.status == 404:
                        # It may have been auto-destructed when the last container was detached.
                        pass
                    else:
                        raise
            except Exception:
                log.exception(f"Failed to destroy the overlay network {network_name}")
        else:
            pass

    async def restart_session(
        self,
        session_creation_id: str,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
    ) -> None:
        log.warning('restart_session({})', session_name_or_id)
        async with self.db.begin_readonly_session() as db_sess:
            session = await self.get_session(
                session_name_or_id,
                access_key,
                load_kernels=True,
                db_session=db_sess,
            )
        session_id = session.id
        kernel_list: List[KernelRow] = session.kernels

        async def _restart_kernel(kernel) -> None:
            loop = asyncio.get_running_loop()
            try:
                kernel_creation_id = secrets.token_urlsafe(16)
                start_future = loop.create_future()
                self.kernel_creation_tracker[
                    kernel.id
                ] = start_future
                try:
                    async with self.db.begin_session() as db_sess:
                        query = (
                            sa.update(KernelRow)
                            .values(status=KernelStatus.RESTARTING)
                            .where(KernelRow.id == kernel.id)
                        )
                        await db_sess.execute(query)
                    async with RPCContext(
                        kernel.agent,       # the main-container's agent
                        kernel.agent_addr,
                        invoke_timeout=None,
                        order_key=None,
                        keepalive_timeout=self.rpc_keepalive_timeout,
                    ) as rpc:
                        updated_config: Dict[str, Any] = {
                            # TODO: support resacling of sub-containers
                        }
                        kernel_info = await rpc.call.restart_kernel(
                            kernel_creation_id,
                            str(kernel.session_id),
                            str(kernel.id),
                            updated_config,
                        )
                    await start_future
                    async with self.db.begin_session() as db_sess:
                        query = (
                            sa.update(KernelRow)
                            .values(
                                status=KernelStatus.RUNNING,
                                container_id=kernel_info['container_id'],
                                repl_in_port=kernel_info['repl_in_port'],
                                repl_out_port=kernel_info['repl_out_port'],
                                stdin_port=kernel_info['stdin_port'],
                                stdout_port=kernel_info['stdout_port'],
                                service_ports=kernel_info.get('service_ports', []),
                            )
                            .where(KernelRow.id == kernel.id)
                        )
                        await db_sess.execute(query)
                finally:
                    del self.kernel_creation_tracker[
                        kernel.id
                    ]
            except Exception:
                log.exception('unexpected-error in _restart_kerenl()')

        restart_coros = []
        for kernel in kernel_list:
            restart_coros.append(_restart_kernel(kernel))
        async with self.handle_kernel_exception(
            'restart_session', session_id, access_key, set_error=True,
        ):
            async with self.db.begin_session() as db_sess:
                query = (
                    sa.update(SessionRow)
                    .values(status=SessionStatus.RESTARTING)
                    .where(SessionRow.id == session_id)
                )
                await db_sess.execute(query)
            await asyncio.gather(*restart_coros)

            async with self.db.begin_session() as db_sess:
                query = (
                    sa.update(SessionRow)
                    .values(status=SessionStatus.RUNNING)
                    .where(SessionRow.id == session_id)
                )
                await db_sess.execute(query)
        # NOTE: If the restarted session is a batch-type one, then the startup command
        #       will be executed again after restart.
        await self.event_producer.produce_event(
            SessionStartedEvent(session_id, session_creation_id),
        )

    async def execute(
        self,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
        api_version: Tuple[int, str],
        run_id: str,
        mode: str,
        code: str,
        opts: Mapping[str, Any],
        *,
        flush_timeout: float = None,
    ) -> Mapping[str, Any]:
        session = await self.get_session(session_name_or_id, access_key, load_kernels=True)
        kernel = session.main_kernel
        async with self.handle_kernel_exception('execute', session.id, access_key):
            # The agent aggregates at most 2 seconds of outputs
            # if the kernel runs for a long time.
            major_api_version = api_version[0]
            if major_api_version == 4:  # manager-agent protocol is same.
                major_api_version = 3
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=30,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.execute(
                    str(kernel.id),
                    major_api_version,
                    run_id, mode, code, opts,
                    flush_timeout,
                )

    async def interrupt_session(
        self,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
    ) -> Mapping[str, Any]:
        session = await self.get_session(session_name_or_id, access_key, load_kernels=True)
        kernel = session.main_kernel
        async with self.handle_kernel_exception('execute', session.id, access_key):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=30,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.interrupt_kernel(str(kernel.id))

    async def get_completions(
        self,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
        text: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        session = await self.get_session(session_name_or_id, access_key, load_kernels=True)
        kernel = session.main_kernel
        async with self.handle_kernel_exception('execute', session.id, access_key):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=10,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.get_completions(str(kernel.id), text, opts)

    async def start_service(
        self,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
        service: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        session = await self.get_session(session_name_or_id, access_key, load_kernels=True)
        kernel = session.main_kernel
        async with self.handle_kernel_exception('execute', session.id, access_key):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=None,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.start_service(str(kernel.id), service, opts)

    async def shutdown_service(
        self,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
        service: str,
    ) -> None:
        session = await self.get_session(session_name_or_id, access_key, load_kernels=True)
        kernel = session.main_kernel
        async with self.handle_kernel_exception('shutdown_service', session.id, access_key):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=None,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.shutdown_service(str(kernel.id), service)

    async def upload_file(
        self,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
        filename: str,
        payload: bytes,
    ) -> Mapping[str, Any]:
        session = await self.get_session(session_name_or_id, access_key, load_kernels=True)
        kernel = session.main_kernel
        async with self.handle_kernel_exception('upload_file', session.id, access_key):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=None,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.upload_file(str(kernel.id), filename, payload)

    async def download_file(
        self,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
        filepath: str,
    ) -> bytes:
        session = await self.get_session(session_name_or_id, access_key, load_kernels=True)
        kernel = session.main_kernel
        async with self.handle_kernel_exception('download_file', session.id,
                                                access_key):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=None,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.download_file(str(kernel.id), filepath)

    async def list_files(
        self,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
        path: str,
    ) -> Mapping[str, Any]:
        session = await self.get_session(session_name_or_id, access_key, load_kernels=True)
        kernel = session.main_kernel
        async with self.handle_kernel_exception('list_files', session.id, access_key):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=30,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.list_files(str(kernel.id), path)

    async def get_logs_from_agent(
        self,
        session_name_or_id: Union[str, SessionId],
        access_key: AccessKey,
    ) -> str:
        session = await self.get_session(session_name_or_id, access_key, load_kernels=True)
        kernel = session.main_kernel
        async with self.handle_kernel_exception('get_logs_from_agent', session.id, access_key):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=30,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                reply = await rpc.call.get_logs(str(kernel.id))
                return reply['logs']

    async def increment_session_usage(
        self,
        session_name: str,
        access_key: AccessKey,
        conn: SAConnection = None,
    ) -> None:
        pass
        # async with reenter_txn(self.db, conn) as conn:
        #     query = (
        #         sa.update(kernels)
        #         .values(num_queries=kernels.c.num_queries + 1)
        #         .where(
        #             (kernels.c.session_name == session_name) &
        #             (kernels.c.access_key == access_key) &
        #             (kernels.c.cluster_role == DEFAULT_ROLE)
        #         )
        #     )
        #     await execute_with_retry(conn, query)

    async def kill_all_sessions_in_agent(self, agent_id, agent_addr):
        async with RPCContext(
            agent_id,
            agent_addr,
            invoke_timeout=None,
            keepalive_timeout=self.rpc_keepalive_timeout,
        ) as rpc:
            coro = rpc.call.clean_all_kernels('manager-freeze-force-kill')
            return await coro

    async def kill_all_sessions(self, db_session=None):
        async with reenter_txn_session(self.db, db_session) as db_sess:
            query = (
                sa.select(AgentRow.id, AgentRow.addr)
                .where(AgentRow.status == AgentStatus.ALIVE)
            )
            result = await db_sess.execute(query)
            rows = result.fetchall()
        tasks = [self.kill_all_sessions_in_agent(ag.id, ag.addr) for ag in rows]
        # async with reenter_txn(self.db, conn, {'postgresql_readonly': True}) as conn:
        #     query = (sa.select([agents.c.id, agents.c.addr])
        #                .where(agents.c.status == AgentStatus.ALIVE))
        #     result = await conn.execute(query)
        #     rows = result.fetchall()
        # tasks = []
        # for row in rows:
        #     tasks.append(
        #         self.kill_all_sessions_in_agent(row['id'], row['addr']),
        #     )
        await asyncio.gather(*tasks, return_exceptions=True)

    async def handle_heartbeat(self, agent_id, agent_info):
        now = datetime.now(tzutc())
        slot_key_and_units = {
            SlotName(k): SlotTypes(v[0]) for k, v in
            agent_info['resource_slots'].items()}
        available_slots = ResourceSlot({
            SlotName(k): Decimal(v[1]) for k, v in
            agent_info['resource_slots'].items()})
        sgroup_name = agent_info.get('scaling_group', 'default')

        async with self.heartbeat_lock:

            instance_rejoin = False

            # Update "last seen" timestamp for liveness tracking
            await redis.execute(
                self.redis_live,
                lambda r: r.hset('agent.last_seen', agent_id, now.timestamp()),
            )

            # Check and update status of the agent record in DB
            async def _update() -> None:
                nonlocal instance_rejoin
                async with self.db.begin_session() as db_sess:
                    agent_row = await get_agent_cols(
                        db_sess,
                        agent_id,
                        cols=[
                            AgentRow.id,
                            AgentRow.status,
                            AgentRow.addr,
                            AgentRow.scaling_group_name,
                            AgentRow.available_slots,
                            AgentRow.version,
                            AgentRow.compute_plugins,
                            AgentRow.architecture,
                        ],
                    )

                    if agent_row is None or agent_row.status is None:
                        # new agent detected!
                        log.info('agent {0} joined!', agent_id)
                        await self.shared_config.update_resource_slots(slot_key_and_units)

                        query = (
                            sa.insert(AgentRow)
                            .values(
                                id=agent_id,
                                status=AgentStatus.ALIVE,
                                region=agent_info['region'],
                                scaling_group_name=sgroup_name,
                                available_slots=available_slots,
                                occupied_slots={},
                                addr=agent_info['addr'],
                                first_contact=now,
                                lost_at=sa.null(),
                                version=agent_info['version'],
                                compute_plugins=agent_info['compute_plugins'],
                                architecture=agent_info.get('architecture', 'x86_64'),
                            )
                        )
                        result = await db_sess.execute(query)
                        assert result.rowcount == 1
                    elif agent_row.status == AgentStatus.ALIVE:
                        agent_map = dict(agent_row)
                        agent_current_data = {
                            **agent_info,
                            'scaling_group_name': sgroup_name,
                            'available_slots': available_slots,
                        }
                        updates = {
                            k: agent_current_data[k] for k in AGENT_UPDATE_FIELDS
                            if agent_current_data[k] != agent_map[k]
                        }
                        if updates:
                            await self.shared_config.update_resource_slots(slot_key_and_units)
                            query = (
                                sa.update(AgentRow)
                                .values(**updates)
                                .where(AgentRow.id == agent_id)
                            )
                            await db_sess.execute(query)
                    elif agent_row.status in (AgentStatus.LOST, AgentStatus.TERMINATED):
                        await self.shared_config.update_resource_slots(slot_key_and_units)
                        instance_rejoin = True
                        query = (
                            sa.update(AgentRow)
                            .values(
                                status=AgentStatus.ALIVE,
                                region=agent_info['region'],
                                scaling_group_name=sgroup_name,
                                addr=agent_info['addr'],
                                lost_at=sa.null(),
                                available_slots=available_slots,
                                version=agent_info['version'],
                                compute_plugins=agent_info['compute_plugins'],
                                architecture=agent_info['architecture'],
                            )
                            .where(AgentRow.id == agent_id)
                        )
                        await db_sess.execute(query)
                    else:
                        log.error('should not reach here! {0}', type(agent_row.status))

            try:
                await execute_with_retry(_update)
            except sa.exc.IntegrityError:
                log.error("Scaling group named [{}] does not exist.", sgroup_name)
                return

            if instance_rejoin:
                await self.event_producer.produce_event(
                    AgentStartedEvent('revived'),
                    source=agent_id,
                )

            # Update the mapping of kernel images to agents.
            known_registries = await get_known_registries(self.shared_config.etcd)
            loaded_images = msgpack.unpackb(snappy.decompress(agent_info['images']))

            def _pipe_builder(r: aioredis.Redis):
                pipe = r.pipeline()
                for image in loaded_images:
                    image_ref = ImageRef(image[0], known_registries, agent_info['architecture'])
                    pipe.sadd(image_ref.canonical, agent_id)
                return pipe
            await redis.execute(self.redis_image, _pipe_builder)

        await self.hook_plugin_ctx.notify(
            'POST_AGENT_HEARTBEAT',
            (agent_id, sgroup_name, available_slots),
        )

    async def mark_agent_terminated(self, agent_id: AgentId, status: AgentStatus) -> None:
        await redis.execute(self.redis_live, lambda r: r.hdel('agent.last_seen', agent_id))

        async def _pipe_builder(r: aioredis.Redis):
            pipe = r.pipeline()
            async for imgname in r.scan_iter():
                pipe.srem(imgname, agent_id)
            return pipe

        async def _update() -> None:
            async with self.db.begin_session() as db_sess:
                fetch_query = (
                    sa.select(AgentRow.status, AgentRow.addr)
                    .where(AgentRow.id == agent_id)
                    .with_for_update()
                )
                result = await db_sess.execute(fetch_query)
                row = result.first()
                prev_status = row.status
                # fetch_query = (
                #     sa.select([
                #         agents.c.status,
                #         agents.c.addr,
                #     ])
                #     .select_from(agents)
                #     .where(agents.c.id == agent_id)
                #     .with_for_update()
                # )
                # result = await conn.execute(fetch_query)
                # row = result.first()
                # prev_status = row['status']
                if prev_status in (None, AgentStatus.LOST, AgentStatus.TERMINATED):
                    return

                now = datetime.now(tzutc())
                update_query = (
                    sa.update(AgentRow)
                    .values(
                        status=status,
                        status_changed=now,
                        lost_at=now,
                    )
                    .where(AgentRow.id == agent_id)
                )
                await db_sess.execute(update_query)
                # update_query = (
                #     sa.update(agents)
                #     .values({
                #         'status': status,
                #         'status_changed': now,
                #         'lost_at': now,
                #     })
                #     .where(agents.c.id == agent_id)
                # )
                # await conn.execute(update_query)

        await redis.execute(self.redis_image, _pipe_builder)
        await execute_with_retry(_update)
        if status == AgentStatus.LOST:
            log.warning('agent {0} heartbeat timeout detected.', agent_id)
        elif status == AgentStatus.TERMINATED:
            log.info('agent {0} has terminated.', agent_id)

    async def set_session_kernel_status(
        self,
        kernel_id: KernelId,
        access_key: AccessKey,
        *,
        status: KernelStatus,
        status_info: str = '',
        status_data: Mapping[str, Any],
        is_single_kernel: bool = False,
    ) -> None:
        now = datetime.now(tzutc())
        data = {
            'status': status,
            'status_info': status_info,
            'kernel_status_data': status_data,
            'session_status_data': sql_json_merge(
                SessionRow.status_data,
                ('kernels', str(kernel_id),),
                obj=status_data,
            ),
            'status_changed': now,
        }

        async def _update() -> None:
            async with self.db.begin_session() as db_sess:
                await update_kernel_status(
                    db_sess,
                    kernel_id,
                    access_key,
                    update_data=UpdatedStatus(**data),
                    is_single_kernel=is_single_kernel,
                )

        await execute_with_retry(_update)

    async def set_kernel_status(
        self, kernel_id: KernelId,
        status: KernelStatus,
        reason: str = '',
    ) -> None:
        assert status != KernelStatus.TERMINATED, \
               'TERMINATED status update must be handled in ' \
               'mark_kernel_terminated()'
        now = datetime.now(tzutc())
        data = {
            'status': status,
            'status_info': reason,
            'status_changed': now,
        }

        async def _update() -> None:
            async with self.db.begin_session() as db_sess:
                await update_kernel_status(
                    db_sess,
                    kernel_id,
                    update_data=UpdatedStatus(**data),
                    is_single_kernel=False,
                )

        await execute_with_retry(_update)

    async def set_session_result(
        self,
        session_id: SessionId,
        success: bool,
        exit_code: int,
    ) -> None:
        # TODO: store exit code?
        result = SessionResult.SUCCESS if success else SessionResult.FAILURE

        async def _update() -> None:
            async with self.db.begin_session() as db_sess:
                query = (
                    sa.update(SessionRow)
                    .where(SessionRow.id == session_id)
                    .values(result=result)
                )
                await db_sess.execute(query)

        await execute_with_retry(_update)

    async def sync_kernel_stats(
        self, kernel_ids: Sequence[KernelId],
    ) -> None:
        per_kernel_updates = {}
        log.debug('sync_kernel_stats(k:{!r})', kernel_ids)
        for kernel_id in kernel_ids:
            raw_kernel_id = str(kernel_id)
            kern_stat = await redis.execute(
                self.redis_stat,
                lambda r: r.get(raw_kernel_id),
            )
            if kern_stat is None:
                log.warning('sync_kernel_stats(k:{}): no statistics updates', kernel_id)
                continue
            else:
                per_kernel_updates[kernel_id] = msgpack.unpackb(kern_stat)

        async def _update():
            async with self.db.begin_session() as db_sess:
                for kernel_id, updates in per_kernel_updates.items():
                    update_query = (
                        sa.update(KernelRow)
                        .where(KernelRow.id == kernel_id)
                        .values(last_stat=updates)
                    )
                    await db_sess.execute(update_query)
        if per_kernel_updates:
            await execute_with_retry(_update)

    async def mark_kernel_terminated(
        self,
        kernel_id: KernelId,
        reason: str,
        exit_code: int = None,
    ) -> None:
        """
        Mark the kernel (individual worker) terminated and release
        the resource slots occupied by it.
        """
        post_task = self._post_kernel_creation_tasks.get(kernel_id, None)
        if post_task is not None and not post_task.done():
            post_task.cancel()
            try:
                await post_task
            except asyncio.CancelledError:
                pass

        kern_stat = await redis.execute(
            self.redis_stat,
            lambda r: r.get(str(kernel_id)),
        )

        async def _update_kernel_status() -> KernelRow | None:
            async with self.db.begin_session(expire_on_commit=False) as db_sess:
                select_query = (
                    sa.select(KernelRow)
                    .where(KernelRow.id == kernel_id)
                    .options(noload('*'))
                )
                result = await db_sess.execute(select_query)
                kernel = result.scalars().first()
                if (
                    kernel is None
                    or kernel.status in (
                        KernelStatus.CANCELLED,
                        KernelStatus.TERMINATED,
                        KernelStatus.RESTARTING,
                    )
                ):
                    # Skip if non-existent, already terminated, or restarting.
                    return None

                # Change the status to TERMINATED.
                # (we don't delete the row for later logging and billing)
                now = datetime.now(tzutc())
                values = {
                    'status': KernelStatus.TERMINATED,
                    'status_info': reason,
                    'status_changed': now,
                    'status_data': sql_json_merge(
                        KernelRow.status_data,
                        ("kernel",),
                        {"exit_code": exit_code},
                    ),
                    'terminated_at': now,
                }
                if kern_stat:
                    values['last_stat'] = msgpack.unpackb(kern_stat)
                await update_kernel_status(db_sess, kernel, update_data=UpdatedStatus(**values))
                select_query = (
                    sa.select(KernelRow)
                    .where(KernelRow.id == kernel_id)
                    .execution_options(populate_existing=True)
                    .options(
                        noload('*'),
                        selectinload(KernelRow.agent).noload('*'),
                    )
                )
                result = await db_sess.execute(select_query)
                return result.scalars().first()


        kernel = await execute_with_retry(_update_kernel_status)
        if kernel is None:
            return

        async def _recalc() -> None:
            assert kernel is not None
            async with self.db.begin_session() as db_sess:
                await recalc_concurrency_used(db_sess, self.redis_stat, kernel.access_key)
                await recalc_agent_resource_occupancy(db_sess, kernel.agent)

        await execute_with_retry(_recalc)

        # Perform statistics sync in a separate transaction block, since
        # it may take a while to fetch stats from Redis.

        await self.sync_kernel_stats([kernel_id])

    async def check_session_terminated(
        self,
        kernel_id: KernelId,
        reason: str,
    ) -> None:

        async def _check_and_mark() -> Tuple[bool, SessionId | None]:
            async with self.db.begin_session() as db_sess:
                session_id_query = (
                    sa.select(
                        KernelRow.session_id,
                    )
                    .select_from(KernelRow)
                    .where(KernelRow.id == kernel_id)
                )
                kernels_query = (
                    sa.select(
                        KernelRow.session_id,
                        KernelRow.status_data,
                        KernelRow.status,
                    )
                    .select_from(KernelRow)
                    .where(
                        (KernelRow.session_id == session_id_query.scalar_subquery()),
                    )
                    .with_for_update()
                )
                result = await db_sess.execute(kernels_query)
                rows = result.fetchall()
                if not rows:
                    return False, None
                session_id = rows[0].session_id
                if nmget(rows[0].status_data, "session.status") == "terminated":
                    # if already marked "session-terminated", skip the rest process
                    return False, session_id
                all_terminated = all(map(
                    lambda row: row.status in (KernelStatus.TERMINATED, KernelStatus.CANCELLED),
                    rows,
                ))
                if all_terminated:
                    update_query = (
                        sa.update(SessionRow)
                        .where(SessionRow.id == session_id)
                        .values(
                            status_data=sql_json_merge(
                                SessionRow.status_data,
                                ('session',),
                                {'status': 'terminated'},
                            ),
                            status=SessionStatus.TERMINATED,
                        )
                    )
                    await db_sess.execute(update_query)

                return all_terminated, session_id

        do_fire_event, session_id = await execute_with_retry(_check_and_mark)
        if session_id is None:
            return
        if do_fire_event:
            await self.event_producer.produce_event(
                SessionTerminatedEvent(session_id, reason),
            )

    async def mark_session_terminated(
        self,
        session_id: SessionId,
        reason: str,
    ) -> None:
        await self.clean_session(session_id)
