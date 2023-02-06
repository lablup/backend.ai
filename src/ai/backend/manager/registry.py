from __future__ import annotations

import asyncio
import copy
import itertools
import logging
import re
import secrets
import time
import typing
import uuid
import weakref
import zlib
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
    TypeAlias,
    Union,
    cast,
)

import aiodocker
import aiotools
import sqlalchemy as sa
import zmq
from async_timeout import timeout as _timeout
from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport
from callosum.rpc import Peer, RPCUserError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dateutil.tz import tzutc
from redis.asyncio import Redis
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import selectinload
from yarl import URL

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.docker import ImageRef, get_known_registries, get_registry_info
from ai.backend.common.events import (
    AgentStartedEvent,
    KernelCancelledEvent,
    KernelLifecycleEventReason,
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
    ClusterSSHPortMapping,
    DeviceId,
    HardwareMetadata,
    KernelEnqueueingConfig,
    KernelId,
    RedisConnectionInfo,
    ResourceSlot,
    SessionEnqueueingConfig,
    SessionId,
    SessionTypes,
    SlotName,
    SlotTypes,
    check_typed_dict,
)

from .api.exceptions import (
    AgentError,
    BackendError,
    GenericForbidden,
    InstanceNotFound,
    InvalidAPIParameters,
    QuotaExceeded,
    RejectedByHook,
    ScalingGroupNotFound,
    SessionNotFound,
)
from .config import SharedConfig
from .defs import DEFAULT_ROLE, INTRINSIC_SLOTS
from .exceptions import MultiAgentError
from .models import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    KERNEL_STATUS_TRANSITION_MAP,
    SESSION_STATUS_TRANSITION_MAP,
    USER_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    AgentRow,
    AgentStatus,
    ImageRow,
    KernelRow,
    KernelStatus,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    SessionDependencyRow,
    SessionRow,
    SessionStatus,
    UserRow,
    agents,
    determine_session_status,
    handle_session_exception,
    kernels,
    prepare_dotfiles,
    prepare_vfolder_mounts,
    query_allowed_sgroups,
    recalc_agent_resource_occupancy,
    recalc_concurrency_used,
    scaling_groups,
)
from .models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
    reenter_txn,
    reenter_txn_session,
    sql_json_merge,
)
from .types import UserScope

if TYPE_CHECKING:
    from sqlalchemy.engine.row import Row
    from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

    from ai.backend.common.events import EventDispatcher, EventProducer

    from .models.storage import StorageSessionManager
    from .scheduler.types import AgentAllocationContext, KernelAgentBinding, SchedulingContext

MSetType: TypeAlias = Mapping[Union[str, bytes], Union[bytes, float, int, str]]
__all__ = ["AgentRegistry", "InstanceNotFound"]

log = BraceStyleAdapter(logging.getLogger("ai.backend.manager.registry"))

SESSION_NAME_LEN_LIMIT = 10
_read_only_txn_opts = {
    "postgresql_readonly": True,
}


class PeerInvoker(Peer):
    class _CallStub:

        _cached_funcs: Dict[str, Callable]
        order_key: ContextVar[Optional[str]]

        def __init__(self, peer: Peer):
            self._cached_funcs = {}
            self.peer = peer
            self.order_key = ContextVar("order_key", default=None)

        def __getattr__(self, name: str):
            if f := self._cached_funcs.get(name, None):
                return f
            else:

                async def _wrapped(*args, **kwargs):
                    request_body = {
                        "args": args,
                        "kwargs": kwargs,
                    }
                    self.peer.last_used = time.monotonic()
                    ret = await self.peer.invoke(name, request_body, order_key=self.order_key.get())
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
    if agent_id is None or addr is None:
        raise InvalidAPIParameters(
            f"expected valid agent id and agent address, got {agent_id=} and {addr=}"
        )
    keepalive_retry_count = 3
    keepalive_interval = keepalive_timeout // keepalive_retry_count
    if keepalive_interval < 2:
        keepalive_interval = 2
    peer = PeerInvoker(
        connect=ZeroMQAddress(addr),
        transport=ZeroMQRPCTransport,
        transport_opts={
            "zsock_opts": {
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
        async with (_timeout(invoke_timeout), peer):
            okey_token = peer.call.order_key.set("")
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
        self.rpc_keepalive_timeout = int(
            shared_config.get("config/network/rpc/keepalive-timeout", "60")
        )

    async def init(self) -> None:
        self.heartbeat_lock = asyncio.Lock()

    async def shutdown(self) -> None:
        pass

    async def get_instance(self, inst_id: AgentId, field=None):
        async with self.db.begin_readonly() as conn:
            cols = [agents.c.id]
            if field is not None:
                cols.append(field)
            query = sa.select(cols).select_from(agents).where(agents.c.id == inst_id)
            result = await conn.execute(query)
            row = result.first()
            if not row:
                raise InstanceNotFound(inst_id)
            return row

    async def enumerate_instances(self, check_shadow=True):

        async with self.db.begin_readonly() as conn:
            query = sa.select("*").select_from(agents)
            if check_shadow:
                query = query.where(agents.c.status == AgentStatus.ALIVE)
            async for row in (await conn.stream(query)):
                yield row

    async def update_instance(self, inst_id, updated_fields):
        async def _update() -> None:
            async with self.db.begin() as conn:
                query = sa.update(agents).values(**updated_fields).where(agents.c.id == inst_id)
                await conn.execute(query)

        await execute_with_retry(_update)

    async def gather_agent_hwinfo(self, instance_id: AgentId) -> Mapping[str, HardwareMetadata]:
        agent = await self.get_instance(instance_id, agents.c.addr)
        async with RPCContext(
            agent["id"],
            agent["addr"],
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
            proxy_name,
            "GET",
            "volume/hwinfo",
            json={"volume": volume_name},
            raise_for_status=True,
        ) as (_, storage_resp):
            return check_typed_dict(
                await storage_resp.json(),
                HardwareMetadata,  # type: ignore  # (python/mypy#9827)
            )

    async def enqueue_session(
        self,
        session_creation_id: str,
        session_name: str,
        access_key: AccessKey,
        session_enqueue_configs: SessionEnqueueingConfig,
        scaling_group: Optional[str],
        session_type: SessionTypes,
        resource_policy: dict,
        *,
        user_scope: UserScope,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        cluster_size: int = 1,
        session_tag: str = None,
        internal_data: dict = None,
        starts_at: datetime = None,
        agent_list: Sequence[str] = None,
        dependency_sessions: Sequence[SessionId] = None,
        callback_url: URL = None,
    ) -> SessionId:

        session_id = SessionId(uuid.uuid4())

        kernel_enqueue_configs: List[KernelEnqueueingConfig] = session_enqueue_configs[
            "kernel_configs"
        ]
        assert len(kernel_enqueue_configs) >= 1
        main_kernel_config = kernel_enqueue_configs[0]
        assert main_kernel_config["cluster_role"] == DEFAULT_ROLE
        session_creation_config: Mapping = session_enqueue_configs["creation_config"]

        # Check keypair resource limit
        if cluster_size > int(resource_policy["max_containers_per_session"]):
            raise QuotaExceeded(
                f"You cannot create session with more than "
                f"{resource_policy['max_containers_per_session']} containers.",
            )

        async with self.db.begin_readonly() as conn:

            checked_scaling_group = await check_scaling_group(
                conn,
                scaling_group,
                session_type,
                access_key,
                user_scope.domain_name,
                user_scope.group_id,
            )
            if scaling_group is None:
                log.warning(
                    f"enqueue_session(s:{session_name}, ak:{access_key}): "
                    f"The client did not specify the scaling group for session; "
                    f"falling back to {checked_scaling_group}",
                )

            use_host_network_query = (
                sa.select([scaling_groups.c.use_host_network])
                .select_from(scaling_groups)
                .where(scaling_groups.c.name == checked_scaling_group)
            )
            use_host_network_result = await conn.execute(use_host_network_query)
            use_host_network = use_host_network_result.scalar()
            # Translate mounts/mount_map into vfolder mounts
            requested_mounts = session_enqueue_configs["creation_config"].get("mounts") or []
            requested_mount_map = session_enqueue_configs["creation_config"].get("mount_map") or {}
            allowed_vfolder_types = await self.shared_config.get_vfolder_types()
            vfolder_mounts = await prepare_vfolder_mounts(
                conn,
                self.storage_manager,
                allowed_vfolder_types,
                user_scope,
                resource_policy,
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
                    "enqueue_session(): replicating kernel_enqueue_config with cluster_size={}",
                    cluster_size,
                )
                # the main_kernel_config is repliacted to sub-containers
                main_kernel_config["cluster_idx"] = 1  # main1
                main_kernel_config["local_rank"] = 0  # main1: 0
                for i in range(cluster_size - 1):
                    sub_kernel_config = cast(KernelEnqueueingConfig, {**main_kernel_config})
                    sub_kernel_config["cluster_role"] = "sub"
                    sub_kernel_config["cluster_idx"] = i + 1  # subN
                    sub_kernel_config["local_rank"] = i + 1  # sub1: 1, sub2: 2, ...
                    sub_kernel_config["cluster_hostname"] = sub_kernel_config["cluster_role"] + str(
                        sub_kernel_config["cluster_idx"]
                    )
                    kernel_enqueue_configs.append(sub_kernel_config)
            elif len(kernel_enqueue_configs) > 1:
                # each container should have its own kernel_config
                log.debug(
                    "enqueue_session(): using given kernel_enqueue_configs with cluster_size={}",
                    cluster_size,
                )
                if len(kernel_enqueue_configs) != cluster_size:
                    raise InvalidAPIParameters(
                        "The number of kernel configs differs from the cluster size"
                    )
            else:
                raise InvalidAPIParameters("Missing kernel configurations")

        # Prepare internal data.
        internal_data = {} if internal_data is None else internal_data
        internal_data.update(dotfile_data)

        hook_result = await self.hook_plugin_ctx.dispatch(
            "PRE_ENQUEUE_SESSION",
            (session_id, session_name, access_key),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)

        session_requested_slots = ResourceSlot()
        session_data = {
            "id": session_id,
            "status": SessionStatus.PENDING,
            "status_history": {
                SessionStatus.PENDING.name: datetime.now(tzutc()).isoformat(),
            },
            "creation_id": session_creation_id,
            "name": session_name,
            "session_type": session_type,
            "cluster_mode": cluster_mode.value,
            "cluster_size": cluster_size,
            "scaling_group_name": checked_scaling_group,
            "domain_name": user_scope.domain_name,
            "group_id": user_scope.group_id,
            "user_uuid": user_scope.user_uuid,
            "access_key": access_key,
            "tag": session_tag,
            "starts_at": starts_at,
            "callback_url": callback_url,
            "occupying_slots": ResourceSlot(),
            "vfolder_mounts": vfolder_mounts,
        }

        kernel_shared_data = {
            "status": KernelStatus.PENDING,
            "status_history": {
                KernelStatus.PENDING.name: datetime.now(tzutc()).isoformat(),
            },
            "session_creation_id": session_creation_id,
            "session_id": session_id,
            "session_name": session_name,
            "session_type": session_type,
            "cluster_mode": cluster_mode.value,
            "cluster_size": cluster_size,
            "scaling_group": checked_scaling_group,
            "domain_name": user_scope.domain_name,
            "group_id": user_scope.group_id,
            "user_uuid": user_scope.user_uuid,
            "access_key": access_key,
            "tag": session_tag,
            "starts_at": starts_at,
            "internal_data": internal_data,
            "callback_url": callback_url,
            "occupied_shares": {},
            "mounts": [mount.name for mount in vfolder_mounts],  # TODO: keep for legacy?
            "vfolder_mounts": vfolder_mounts,
            "repl_in_port": 0,
            "repl_out_port": 0,
            "stdin_port": 0,
            "stdout_port": 0,
            "preopen_ports": sa.bindparam("preopen_ports"),
            "use_host_network": use_host_network,
        }

        kernel_data = []

        for idx, kernel in enumerate(kernel_enqueue_configs):
            kernel_id = KernelId(uuid.uuid4())
            creation_config = kernel["creation_config"]
            image_ref = kernel["image_ref"]
            resource_opts = creation_config.get("resource_opts") or {}

            creation_config["mounts"] = [vfmount.to_json() for vfmount in vfolder_mounts]
            # TODO: merge into a single call
            async with self.db.begin_readonly_session() as session:
                log.debug(
                    "enqueue_session(): image ref => {} ({})", image_ref, image_ref.architecture
                )
                image_row = await ImageRow.resolve(session, [image_ref])
            image_min_slots, image_max_slots = await image_row.get_slot_ranges(self.shared_config)
            known_slot_types = await self.shared_config.get_resource_slots()

            labels = image_row.labels
            # Parse service ports to check for port errors
            parse_service_ports(labels.get("ai.backend.service-ports", ""), BackendError)

            # Shared memory.
            # We need to subtract the amount of shared memory from the memory limit of
            # a container, since tmpfs including /dev/shm uses host-side kernel memory
            # and cgroup's memory limit does not apply.
            shmem = resource_opts.get("shmem", None)
            if shmem is None:
                shmem = labels.get("ai.backend.resource.preferred.shmem", "64m")
            shmem = BinarySize.from_str(shmem)
            resource_opts["shmem"] = shmem
            image_min_slots = copy.deepcopy(image_min_slots)
            image_min_slots["mem"] += shmem

            # Sanitize user input: does it have resource config?
            if "resources" in creation_config:
                # Sanitize user input: does it have "known" resource slots only?
                for slot_key, slot_value in creation_config["resources"].items():
                    if slot_key not in known_slot_types:
                        raise InvalidAPIParameters(f"Unknown requested resource slot: {slot_key}")
                try:
                    requested_slots = ResourceSlot.from_user_input(
                        creation_config["resources"], known_slot_types
                    )
                except ValueError:
                    log.exception("request_slots & image_slots calculation error")
                    # happens when requested_slots have more keys
                    # than the image-defined slots
                    # (e.g., image does not support accelerators
                    #  requested by the client)
                    raise InvalidAPIParameters(
                        "Your resource request has resource type(s) " "not supported by the image."
                    )

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
                cpu = creation_config.get("instanceCores")
                if cpu is None:  # the key is there but may be null.
                    cpu = image_min_slots["cpu"]
                mem = creation_config.get("instanceMemory")
                if mem is None:  # the key is there but may be null.
                    mem = image_min_slots["mem"]
                else:
                    # In legacy clients, memory is normalized to GiB.
                    mem = str(mem) + "g"
                requested_slots = ResourceSlot.from_user_input(
                    {
                        "cpu": cpu,
                        "mem": mem,
                    },
                    known_slot_types,
                )
                gpu = creation_config.get("instanceGPUs")
                if gpu is not None:
                    raise InvalidAPIParameters("Client upgrade required " "to use GPUs (v19.03+).")
                tpu = creation_config.get("instanceTPUs")
                if tpu is not None:
                    raise InvalidAPIParameters("Client upgrade required " "to use TPUs (v19.03+).")

            # Check the image resource slots.
            log_fmt = "s:{} k:{} r:{}-{}"
            log_args = (session_id, kernel_id, kernel["cluster_role"], kernel["cluster_idx"])
            log.debug(log_fmt + " -> requested_slots: {}", *log_args, requested_slots)
            log.debug(log_fmt + " -> resource_opts: {}", *log_args, resource_opts)
            log.debug(log_fmt + " -> image_min_slots: {}", *log_args, image_min_slots)
            log.debug(log_fmt + " -> image_max_slots: {}", *log_args, image_max_slots)

            # Check if: requested >= image-minimum
            if image_min_slots > requested_slots:
                raise InvalidAPIParameters(
                    "Your resource request is smaller than "
                    "the minimum required by the image. ({})".format(
                        " ".join(
                            f"{k}={v}"
                            for k, v in image_min_slots.to_humanized(known_slot_types).items()
                        )
                    )
                )

            # Check if: requested <= image-maximum
            if not (requested_slots <= image_max_slots):
                raise InvalidAPIParameters(
                    "Your resource request is larger than "
                    "the maximum allowed by the image. ({})".format(
                        " ".join(
                            f"{k}={v}"
                            for k, v in image_max_slots.to_humanized(known_slot_types).items()
                        )
                    )
                )

            # Check if: shmem < memory
            if shmem >= requested_slots["mem"]:
                raise InvalidAPIParameters(
                    "Shared memory should be less than the main memory. (s:{}, m:{})".format(
                        str(shmem), str(BinarySize(requested_slots["mem"]))
                    ),
                )

            # Add requested resource slot data to session
            session_requested_slots += requested_slots

            environ = session_creation_config.get("environ") or {}

            # Create kernel object in PENDING state.
            mapped_agent = None
            if not agent_list:
                pass
            else:
                mapped_agent = agent_list[idx]

            kernel_data.append(
                {
                    **kernel_shared_data,
                    "id": kernel_id,
                    "agent": mapped_agent,
                    "cluster_role": kernel["cluster_role"],
                    "cluster_idx": kernel["cluster_idx"],
                    "local_rank": kernel["local_rank"],
                    "cluster_hostname": f"{kernel['cluster_role']}{kernel['cluster_idx']}"
                    if not kernel["cluster_hostname"]
                    else kernel["cluster_hostname"],
                    "image": image_ref.canonical,
                    # "image_id": image_row.id,
                    "architecture": image_ref.architecture,
                    "registry": image_ref.registry,
                    "startup_command": kernel.get("startup_command"),
                    "occupied_slots": ResourceSlot(),
                    "requested_slots": requested_slots,
                    "resource_opts": resource_opts,
                    "environ": [f"{k}={v}" for k, v in environ.items()],
                    "bootstrap_script": kernel.get("bootstrap_script"),
                    "preopen_ports": creation_config.get("preopen_ports", []),
                }
            )

        try:

            async def _enqueue() -> None:
                async with self.db.begin_session() as db_sess:
                    session_data["requested_slots"] = session_requested_slots
                    session = SessionRow(**session_data)
                    kernels = [KernelRow(**kernel) for kernel in kernel_data]
                    db_sess.add(session)
                    db_sess.add_all(kernels)

                    if not dependency_sessions:
                        return

                    matched_dependency_session_ids = []
                    for dependency_id in dependency_sessions:
                        try:
                            match_info = await SessionRow.get_session(
                                dependency_id,
                                access_key,
                                db_session=db_sess,
                            )
                        except SessionNotFound:
                            raise InvalidAPIParameters(
                                "Unknown session ID or name in the dependency list",
                                extra_data={"session_ref": dependency_id},
                            )
                        else:
                            matched_dependency_session_ids.append(match_info.id)

                    dependency_rows = [
                        SessionDependencyRow(session_id=session_id, depends_on=depend_id)
                        for depend_id in matched_dependency_session_ids
                    ]
                    db_sess.add_all(dependency_rows)
                    await db_sess.commit()

            await execute_with_retry(_enqueue)
        except DBAPIError as e:
            if getattr(e.orig, "pgcode", None) == "23503":
                match = re.search(r"Key \(agent\)=\((?P<agent>[^)]+)\)", repr(e.orig))
                if match:
                    raise InvalidAPIParameters(f"No such agent: {match.group('agent')}")
                else:
                    raise InvalidAPIParameters("No such agent")
            raise

        await self.hook_plugin_ctx.notify(
            "POST_ENQUEUE_SESSION",
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
        from .scheduler.types import AgentAllocationContext, KernelAgentBinding

        kernel_agent_bindings: Sequence[KernelAgentBinding] = [
            KernelAgentBinding(
                kernel=k,
                agent_alloc_ctx=AgentAllocationContext(
                    agent_id=k.agent,
                    agent_addr=k.agent_addr,
                    scaling_group=scheduled_session.scaling_group,
                ),
                allocated_host_ports=set(),
            )
            for k in scheduled_session.kernels
        ]
        session_creation_id = scheduled_session.creation_id

        hook_result = await self.hook_plugin_ctx.dispatch(
            "PRE_START_SESSION",
            (
                scheduled_session.id,
                scheduled_session.name,
                scheduled_session.access_key,
            ),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)

        # Get resource policy for the session
        # TODO: memoize with TTL
        async with self.db.begin_readonly_session() as db_sess:
            resouce_policy_q = sa.select(KeyPairRow.resource_policy).where(
                KeyPairRow.access_key == scheduled_session.access_key
            )
            query = sa.select(KeyPairResourcePolicyRow).where(
                KeyPairResourcePolicyRow.name == resouce_policy_q.scalar_subquery()
            )
            result = await db_sess.execute(query)
            resource_policy = result.scalars().first()
        auto_pull = await self.shared_config.get_raw("config/docker/image/auto_pull")

        # Aggregate image registry information
        keyfunc = lambda item: item.kernel.image_ref
        image_infos: MutableMapping[str, ImageRow] = {}
        async with self.db.begin_readonly_session() as session:
            for image_ref, _ in itertools.groupby(
                sorted(kernel_agent_bindings, key=keyfunc),
                key=keyfunc,
            ):
                # img_query = sa.select(ImageRow).where(ImageRow.id == image_id)
                # img_row: ImageRow = (await session.execute(img_query)).scalars().first()
                # image_ref = img_row.image_ref
                log.debug(
                    "start_session(): image ref => {} ({})", image_ref, image_ref.architecture
                )
                image_infos[str(image_ref)] = await ImageRow.resolve(session, [image_ref])
                registry_url, registry_creds = await get_registry_info(
                    self.shared_config.etcd, image_ref.registry
                )
        image_info = {
            "image_infos": image_infos,
            "registry_url": registry_url,
            "registry_creds": registry_creds,
            "resource_policy": resource_policy,
            "auto_pull": auto_pull,
        }

        network_name: Optional[str] = None
        cluster_ssh_port_mapping: Optional[Dict[str, Tuple[str, int]]] = None
        if not scheduled_session.use_host_network:
            if scheduled_session.cluster_mode == ClusterMode.SINGLE_NODE:
                if scheduled_session.cluster_size > 1:
                    network_name = f"bai-singlenode-{scheduled_session.id}"
                    assert kernel_agent_bindings[0].agent_alloc_ctx.agent_id is not None
                    assert scheduled_session.id is not None
                    try:
                        async with RPCContext(
                            kernel_agent_bindings[0].agent_alloc_ctx.agent_id,
                            kernel_agent_bindings[0].agent_alloc_ctx.agent_addr,
                            invoke_timeout=None,
                            order_key=str(scheduled_session.main_kernel.id),
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
                network_name = f"bai-multinode-{scheduled_session.id}"
                mtu = await self.shared_config.get_raw("config/network/overlay/mtu")
                try:
                    # Overlay networks can only be created at the Swarm manager.
                    create_options = {
                        "Name": network_name,
                        "Driver": "overlay",
                        "Attachable": True,
                        "Labels": {
                            "ai.backend.cluster-network": "1",
                        },
                        "Options": {},
                    }
                    if mtu:
                        create_options["Options"] = {"com.docker.network.driver.mtu": mtu}
                    await self.docker.networks.create(create_options)
                except Exception:
                    log.exception(f"Failed to create an overlay network {network_name}")
                    raise
        else:
            network_name = "host"
            if scheduled_session.cluster_size > 1:
                keyfunc = lambda item: item.kernel.cluster_role
                cluster_ssh_port_mapping = {}
                for cluster_role, group_iterator in itertools.groupby(
                    sorted(kernel_agent_bindings, key=keyfunc),
                    key=keyfunc,
                ):
                    for index, item in enumerate(group_iterator):
                        assert item.agent_alloc_ctx.agent_id is not None
                        async with RPCContext(
                            item.agent_alloc_ctx.agent_id,
                            item.agent_alloc_ctx.agent_addr,
                            invoke_timeout=None,
                            order_key=str(scheduled_session.id),
                            keepalive_timeout=self.rpc_keepalive_timeout,
                        ) as rpc:
                            port = await rpc.call.assign_port()
                            agent_addr = item.agent_alloc_ctx.agent_addr.replace(
                                "tcp://", ""
                            ).split(":", maxsplit=1)[0]
                            cluster_ssh_port_mapping[item.kernel.cluster_hostname] = (
                                agent_addr,
                                port,
                            )
                            item.allocated_host_ports.add(port)
        log.debug("ssh connection info mapping: {}", cluster_ssh_port_mapping)

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
                if scheduled_session.cluster_size > 1
                else None
            ),
            cluster_ssh_port_mapping=cast(
                Optional[ClusterSSHPortMapping], cluster_ssh_port_mapping
            ),
        )
        scheduled_session.environ.update(
            {
                "BACKENDAI_SESSION_ID": str(scheduled_session.id),
                "BACKENDAI_SESSION_NAME": str(scheduled_session.name),
                "BACKENDAI_CLUSTER_SIZE": str(scheduled_session.cluster_size),
                "BACKENDAI_CLUSTER_REPLICAS": ",".join(f"{k}:{v}" for k, v in replicas.items()),
                "BACKENDAI_CLUSTER_HOSTS": ",".join(
                    binding.kernel.cluster_hostname for binding in kernel_agent_bindings
                ),
                "BACKENDAI_ACCESS_KEY": scheduled_session.access_key,
                # BACKENDAI_SERVICE_PORTS are set as per-kernel env-vars.
                # (In the future, each kernel in a cluster session may use different images)
                "BACKENDAI_PREOPEN_PORTS": ",".join(
                    str(port) for port in scheduled_session.main_kernel.preopen_ports
                )
                if scheduled_session.main_kernel.preopen_ports is not None
                else "",
            }
        )

        # Aggregate by agents to minimize RPC calls
        per_agent_tasks = []
        keyfunc = lambda item: item.agent_alloc_ctx.agent_id
        for agent_id, group_iterator in itertools.groupby(
            sorted(kernel_agent_bindings, key=keyfunc),
            key=keyfunc,
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
        # If all is well, let's say the session is ready.
        await self.event_producer.produce_event(
            SessionStartedEvent(scheduled_session.id, session_creation_id),
        )
        await self.hook_plugin_ctx.notify(
            "POST_START_SESSION",
            (
                scheduled_session.id,
                scheduled_session.name,
                scheduled_session.access_key,
            ),
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
                    if (
                        isinstance(allocation, (BinarySize, str))
                        and BinarySize.suffix_map.get(allocation[-1].lower()) is not None
                    ):
                        total_allocs.append(Decimal(BinarySize.from_str(allocation)))
                    else:  # maybe Decimal("Infinity"), etc.
                        total_allocs.append(Decimal(allocation))
                slots[slot_name] = str(sum(total_allocs))
        return slots

    async def finalize_running(self, created_info: Mapping[str, Any]) -> None:
        async def _finalize_running() -> Optional[SessionId]:
            # Record kernel access information
            try:
                async with self.db.begin() as conn:
                    kernel_query = (
                        sa.select(kernels.c.status)
                        .where(kernels.c.id == created_info["id"])
                        .with_for_update(skip_locked=True)
                    )
                    current_status = (await conn.execute(kernel_query)).scalar()
                    # current_status is None when kernel_query is locked by concurrent query.
                    if (
                        current_status is None
                        or KernelStatus.RUNNING not in KERNEL_STATUS_TRANSITION_MAP[current_status]
                    ):
                        return None
                    agent_host = URL(created_info["agent_addr"]).host
                    kernel_host = created_info.get("kernel_host", agent_host)
                    service_ports = created_info.get("service_ports", [])
                    # NOTE: created_info contains resource_spec
                    values = {
                        "scaling_group": created_info["scaling_group"],
                        "status": KernelStatus.RUNNING,
                        "container_id": created_info["container_id"],
                        "occupied_shares": {},
                        "attached_devices": created_info.get("attached_devices", {}),
                        "kernel_host": kernel_host,
                        "repl_in_port": created_info["repl_in_port"],
                        "repl_out_port": created_info["repl_out_port"],
                        "stdin_port": created_info["stdin_port"],
                        "stdout_port": created_info["stdout_port"],
                        "service_ports": service_ports,
                        "status_history": sql_json_merge(
                            kernels.c.status_history,
                            (),
                            {
                                KernelStatus.RUNNING.name: datetime.now(tzutc()).isoformat(),
                            },
                        ),
                    }
                    actual_allocs = self.convert_resource_spec_to_resource_slot(
                        created_info["resource_spec"]["allocations"]
                    )
                    values["occupied_slots"] = actual_allocs
                    self._kernel_actual_allocated_resources[created_info["id"]] = actual_allocs
                    update_query = (
                        sa.update(kernels)
                        .values(values)
                        .where(kernels.c.id == created_info["id"])
                        .returning(kernels.c.session_id)
                    )
                    return (await conn.execute(update_query)).first()["session_id"]
            except Exception:
                log.exception("error while executing _finalize_running")
                raise

        session_id = await execute_with_retry(_finalize_running)
        if session_id is None:
            return None

        async def _check_session() -> None:
            async with self.db.begin_session() as db_sess:
                query = (
                    sa.select(SessionRow)
                    .where(SessionRow.id == session_id)
                    .options(selectinload(SessionRow.kernels))
                )
                result = await db_sess.execute(query)
                session: SessionRow = result.scalars().first()
                candidate_status = determine_session_status(session.kernels)
                if candidate_status in SESSION_STATUS_TRANSITION_MAP[session.status]:
                    update_query = (
                        sa.update(SessionRow)
                        .where(SessionRow.id == session_id)
                        .values(
                            status=candidate_status,
                            status_history=sql_json_merge(
                                SessionRow.status_history,
                                (),
                                {
                                    SessionStatus.RUNNING.name: datetime.now(tzutc()).isoformat(),
                                },
                            ),
                        )
                    )
                    await db_sess.execute(update_query)

        await execute_with_retry(_check_session)

    async def _post_create_kernel(
        self,
        agent_alloc_ctx: AgentAllocationContext,
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
            await self.finalize_running(
                {
                    **created_info,
                    "scaling_group": agent_alloc_ctx.scaling_group,
                    "agent_addr": agent_alloc_ctx.agent_addr,
                }
            )

        finally:
            try:
                await asyncio.sleep(1)
            finally:
                del self._post_kernel_creation_infos[kernel_id]
                del self.kernel_creation_tracker[kernel_id]

    async def _create_kernels_in_one_agent(
        self,
        agent_alloc_ctx: AgentAllocationContext,
        scheduled_session: SessionRow,
        items: Sequence[KernelAgentBinding],
        image_info: Mapping[str, Any],
        cluster_info,
    ) -> None:
        loop = asyncio.get_running_loop()
        registry_url = image_info["registry_url"]
        registry_creds = image_info["registry_creds"]
        image_infos = image_info["image_infos"]
        resource_policy: KeyPairResourcePolicyRow = image_info["resource_policy"]
        auto_pull = image_info["auto_pull"]
        assert agent_alloc_ctx.agent_id is not None
        assert scheduled_session.id is not None
        async with RPCContext(
            agent_alloc_ctx.agent_id,
            agent_alloc_ctx.agent_addr,
            invoke_timeout=None,
            order_key=str(scheduled_session.id),
            keepalive_timeout=self.rpc_keepalive_timeout,
        ) as rpc:
            kernel_creation_id = secrets.token_urlsafe(16)
            # Prepare kernel_started event handling
            for binding in items:
                self.kernel_creation_tracker[binding.kernel.id] = loop.create_future()
            # Spawn post-processing tasks
            post_tasks = []
            for binding in items:
                self._post_kernel_creation_infos[binding.kernel.id] = loop.create_future()
                post_task = asyncio.create_task(
                    self._post_create_kernel(
                        agent_alloc_ctx,
                        binding.kernel.id,
                    )
                )
                self._post_kernel_creation_tasks[binding.kernel.id] = post_task
                post_tasks.append(post_task)
            try:
                get_image_ref = lambda k: image_infos[str(k.image_ref)].image_ref
                # Issue a batched RPC call to create kernels on this agent
                created_infos = await rpc.call.create_kernels(
                    kernel_creation_id,
                    str(scheduled_session.id),
                    [str(binding.kernel.id) for binding in items],
                    [
                        {
                            "image": {
                                "registry": {
                                    "name": get_image_ref(binding.kernel).registry,
                                    "url": str(registry_url),
                                    **registry_creds,  # type: ignore
                                },
                                "digest": image_infos[binding.kernel.image].config_digest,
                                "repo_digest": None,
                                "canonical": get_image_ref(binding.kernel).canonical,
                                "architecture": get_image_ref(binding.kernel).architecture,
                                "labels": image_infos[binding.kernel.image].labels,
                            },
                            "session_type": scheduled_session.session_type.value,
                            "cluster_role": binding.kernel.cluster_role,
                            "cluster_idx": binding.kernel.cluster_idx,
                            "local_rank": binding.kernel.local_rank,
                            "cluster_hostname": binding.kernel.cluster_hostname,
                            "idle_timeout": resource_policy.idle_timeout,
                            "mounts": [item.to_json() for item in scheduled_session.vfolder_mounts],
                            "environ": {
                                # inherit per-session environment variables
                                **scheduled_session.environ,
                                # set per-kernel environment variables
                                "BACKENDAI_KERNEL_ID": str(binding.kernel.id),
                                "BACKENDAI_KERNEL_IMAGE": str(get_image_ref(binding.kernel)),
                                "BACKENDAI_CLUSTER_ROLE": binding.kernel.cluster_role,
                                "BACKENDAI_CLUSTER_IDX": str(binding.kernel.cluster_idx),
                                "BACKENDAI_CLUSTER_LOCAL_RANK": str(binding.kernel.local_rank),
                                "BACKENDAI_CLUSTER_HOST": str(binding.kernel.cluster_hostname),
                                "BACKENDAI_SERVICE_PORTS": str(
                                    image_infos[binding.kernel.image].labels.get(
                                        "ai.backend.service-ports"
                                    )
                                ),
                            },
                            "resource_slots": binding.kernel.requested_slots.to_json(),
                            "resource_opts": binding.kernel.resource_opts,
                            "bootstrap_script": binding.kernel.bootstrap_script,
                            "startup_command": binding.kernel.startup_command,
                            "internal_data": scheduled_session.main_kernel.internal_data,
                            "auto_pull": auto_pull,
                            "preopen_ports": scheduled_session.main_kernel.preopen_ports,
                            "allocated_host_ports": list(binding.allocated_host_ports),
                            "agent_addr": binding.agent_alloc_ctx.agent_addr,
                            "scaling_group": binding.agent_alloc_ctx.scaling_group,
                        }
                        for binding in items
                    ],
                    cluster_info,
                )
                log.debug(
                    "start_session(s:{}, ak:{}, k:{}) -> created on ag:{}",
                    scheduled_session.name,
                    scheduled_session.access_key,
                    [binding.kernel.id for binding in items],
                    agent_alloc_ctx.agent_id,
                )
                # Pass the return value of RPC calls to post-processing tasks
                for created_info in created_infos:
                    kernel_id = KernelId(uuid.UUID(created_info["id"]))
                    self._post_kernel_creation_infos[kernel_id].set_result(created_info)
                await asyncio.gather(*post_tasks, return_exceptions=True)
            except (asyncio.TimeoutError, asyncio.CancelledError) as e:
                for binding in items:
                    kernel_id = binding.kernel.kernel_id
                    self.kernel_creation_tracker[kernel_id].cancel()
                    self._post_kernel_creation_infos[kernel_id].set_exception(e)
                await asyncio.gather(*post_tasks, return_exceptions=True)
            except Exception as e:
                # The agent has already cancelled or issued the destruction lifecycle event
                # for this batch of kernels.
                for binding in items:
                    kernel_id = binding.kernel.id
                    self.kernel_creation_tracker[kernel_id].cancel()
                    self._post_kernel_creation_infos[kernel_id].set_exception(e)
                    ex = e

                    async def _update_failure() -> None:
                        async with self.db.begin_session() as db_sess:
                            now = datetime.now(tzutc())
                            query = (
                                sa.update(KernelRow)
                                .where(KernelRow.id == kernel_id)
                                .value(
                                    status=KernelStatus.ERROR,
                                    status_info=f"other-error ({ex!r})",
                                    status_changed=now,
                                    terminated_at=now,
                                    status_history=sql_json_merge(
                                        KernelRow.status_history,
                                        (),
                                        {
                                            KernelStatus.ERROR.name: now.isoformat(),  # ["PULLING", "PREPARING"]
                                        },
                                    ),
                                    agent=binding.agent_alloc_ctx.agent_id,
                                    agent_addr=binding.agent_alloc_ctx.agent_addr,
                                    scaling_group=binding.agent_alloc_ctx.scaling_group,
                                    status_data={
                                        "error": {
                                            "src": "other",
                                            "name": ex.__class__.__name__,
                                            "repr": repr(ex),
                                        },
                                    },
                                )
                            )
                            await db_sess.execute(query)

                    await execute_with_retry(_update_failure)
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
        public_key += b" work@cluster.backend.ai.local"
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return {
            "private_key": pem.decode("utf-8"),
            "public_key": public_key.decode("utf-8"),
        }

    async def get_keypair_occupancy(self, access_key, *, db_sess=None):
        known_slot_types = await self.shared_config.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                query = sa.select(KernelRow.occupied_slots).where(
                    (KernelRow.access_key == access_key)
                    & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                )
                zero = ResourceSlot()
                key_occupied = sum(
                    [row.occupied_slots async for row in (await _sess.stream(query))], zero
                )
                # drop no-longer used slot types
                drops = [k for k in key_occupied.keys() if k not in known_slot_types]
                for k in drops:
                    del key_occupied[k]
                return key_occupied

        return await execute_with_retry(_query)

    async def get_domain_occupancy(self, domain_name, *, db_sess=None):
        # TODO: store domain occupied_slots in Redis?
        known_slot_types = await self.shared_config.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                query = sa.select(KernelRow.occupied_slots).where(
                    (KernelRow.domain_name == domain_name)
                    & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                )
                zero = ResourceSlot()
                key_occupied = sum(
                    [row.occupied_slots async for row in (await _sess.stream(query))],
                    zero,
                )
                # drop no-longer used slot types
                drops = [k for k in key_occupied.keys() if k not in known_slot_types]
                for k in drops:
                    del key_occupied[k]
                return key_occupied

        return await execute_with_retry(_query)

    async def get_group_occupancy(self, group_id, *, db_sess=None):
        # TODO: store domain occupied_slots in Redis?
        known_slot_types = await self.shared_config.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                query = sa.select(KernelRow.occupied_slots).where(
                    (KernelRow.group_id == group_id)
                    & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES)),
                )
                zero = ResourceSlot()
                key_occupied = sum(
                    [row.occupied_slots async for row in (await _sess.stream(query))],
                    zero,
                )
                # drop no-longer used slot types
                drops = [k for k in key_occupied.keys() if k not in known_slot_types]
                for k in drops:
                    del key_occupied[k]
                return key_occupied

        return await execute_with_retry(_query)

    async def update_scaling_group(self, id, scaling_group) -> None:
        agent = await self.get_instance(id, agents.c.addr)
        async with RPCContext(
            agent["id"],
            agent["addr"],
            invoke_timeout=None,
            keepalive_timeout=self.rpc_keepalive_timeout,
        ) as rpc:
            await rpc.call.update_scaling_group(scaling_group)

    async def settle_agent_alloc(
        self,
        kernel_agent_bindings: Sequence[KernelAgentBinding],
    ) -> None:
        """
        Tries to settle down agent row's occupied_slots with real value. This must be called
        after kernel creation is completed, to prevent fraction of resource dropped by agent scheduler
        during kernel creation still being reported as used.
        """

        keyfunc = lambda item: item.agent_alloc_ctx.agent_id
        for agent_id, group_iterator in itertools.groupby(
            sorted(kernel_agent_bindings, key=keyfunc),
            key=keyfunc,
        ):
            actual_allocated_slots = ResourceSlot()
            requested_slots = ResourceSlot()

            for kernel_agent_binding in group_iterator:
                # this value must be set while running _post_create_kernel
                actual_allocated_slot = self._kernel_actual_allocated_resources.get(
                    kernel_agent_binding.kernel.id
                )
                requested_slots += kernel_agent_binding.kernel.requested_slots
                if actual_allocated_slot is not None:
                    actual_allocated_slots += ResourceSlot.from_json(actual_allocated_slot)
                    del self._kernel_actual_allocated_resources[kernel_agent_binding.kernel.id]
                else:  # something's wrong; just fall back to requested slot value
                    actual_allocated_slots += kernel_agent_binding.kernel.requested_slots

            # perform DB update only if requested slots and actual allocated value differs
            if actual_allocated_slots != requested_slots:
                log.debug("calibrating resource slot usage for agent {}", agent_id)
                async with self.db.begin_session() as db_sess:
                    select_query = sa.select(AgentRow.occupied_slots).where(AgentRow.id == agent_id)
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
        occupied_slots_per_agent: MutableMapping[str, ResourceSlot] = defaultdict(
            lambda: ResourceSlot({"cpu": 0, "mem": 0})
        )

        async def _recalc() -> None:
            async with self.db.begin() as conn:
                # Query running containers and calculate concurrency_used per AK and
                # occupied_slots per agent.
                query = (
                    sa.select([kernels.c.access_key, kernels.c.agent, kernels.c.occupied_slots])
                    .where(kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                    .order_by(sa.asc(kernels.c.access_key))
                )
                async for row in (await conn.stream(query)):
                    occupied_slots_per_agent[row.agent] += ResourceSlot(row.occupied_slots)
                query = (
                    sa.select([kernels.c.access_key, kernels.c.agent, kernels.c.occupied_slots])
                    .where(kernels.c.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                    .order_by(sa.asc(kernels.c.access_key))
                )
                async for row in (await conn.stream(query)):
                    concurrency_used_per_key[row.access_key] += 1

                if len(occupied_slots_per_agent) > 0:
                    # Update occupied_slots for agents with running containers.
                    for aid, slots in occupied_slots_per_agent.items():
                        query = (
                            sa.update(agents).values(occupied_slots=slots).where(agents.c.id == aid)
                        )
                        await conn.execute(query)
                    # Update all other agents to have empty occupied_slots.
                    query = (
                        sa.update(agents)
                        .values(occupied_slots=ResourceSlot({}))
                        .where(agents.c.status == AgentStatus.ALIVE)
                        .where(sa.not_(agents.c.id.in_(occupied_slots_per_agent.keys())))
                    )
                    await conn.execute(query)
                else:
                    query = (
                        sa.update(agents)
                        .values(occupied_slots=ResourceSlot({}))
                        .where(agents.c.status == AgentStatus.ALIVE)
                    )
                    await conn.execute(query)

        await execute_with_retry(_recalc)

        # Update keypair resource usage for keypairs with running containers.
        kp_key = "keypair.concurrency_used"

        async def _update(r: Redis):
            updates = {
                f"{kp_key}.{k}": concurrency_used_per_key[k] for k in concurrency_used_per_key
            }
            if updates:
                await r.mset(typing.cast(MSetType, updates))

        async def _update_by_fullscan(r: Redis):
            updates = {}
            keys = await r.keys(f"{kp_key}.*")
            for ak in keys:
                usage = concurrency_used_per_key.get(ak, 0)
                updates[f"{kp_key}.{ak}"] = usage
            if updates:
                await r.mset(typing.cast(MSetType, updates))

        if do_fullscan:
            await redis_helper.execute(
                self.redis_stat,
                _update_by_fullscan,
            )
        else:
            await redis_helper.execute(
                self.redis_stat,
                _update,
            )

    async def destroy_session_lowlevel(
        self,
        session_id: SessionId,
        kernels: Sequence[
            Mapping[str, Any]
        ],  # should have (id, agent, agent_addr, container_id) columns
    ) -> None:
        """
        Destroy the kernels that belongs the to given session unconditionally
        and without generation of any relevant events nor invocation of plugin hooks.
        """
        keyfunc = lambda item: item["agent"] if item["agent"] is not None else ""
        for agent_id, group_iterator in itertools.groupby(
            sorted(kernels, key=keyfunc),
            key=keyfunc,
        ):
            rpc_coros = []
            destroyed_kernels: List[Mapping[str, Any]] = []
            grouped_kernels = [*group_iterator]
            kernel: Mapping[str, Any]
            for kernel in grouped_kernels:
                if kernel.get("container_id") is not None and kernel.get("agent_addr") is not None:
                    destroyed_kernels.append(kernel)
            if not destroyed_kernels:
                return
            async with RPCContext(
                destroyed_kernels[0]["agent"],
                destroyed_kernels[0]["agent_addr"],
                invoke_timeout=None,
                order_key=str(session_id),
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                for kernel in destroyed_kernels:
                    # internally it enqueues a "destroy" lifecycle event.
                    rpc_coros.append(
                        rpc.call.destroy_kernel(
                            str(kernel["id"]),
                            KernelLifecycleEventReason.FAILED_TO_START,
                            suppress_events=True,
                        ),
                    )
                await asyncio.gather(*rpc_coros)

    async def destroy_session(
        self,
        session: SessionRow,
        *,
        forced: bool = False,
        reason: Optional[KernelLifecycleEventReason] = None,
    ) -> Mapping[str, Any]:
        """
        Destroy session kernels. Do not destroy
        PREPARING/TERMINATING/ERROR and PULLING sessions.

        :param forced: If True, destroy PREPARING/TERMINATING/ERROR session.
                       However, PULLING session still cannot be destroyed.
        :param reason: Reason to destroy a session if client wants to specify it manually.
        """
        session_id = session.id
        if not reason:
            reason = (
                KernelLifecycleEventReason.FORCE_TERMINATED
                if forced
                else KernelLifecycleEventReason.USER_REQUESTED
            )
        hook_result = await self.hook_plugin_ctx.dispatch(
            "PRE_DESTROY_SESSION",
            (session_id, session.name, session.access_key),
            return_when=ALL_COMPLETED,
        )
        if hook_result.status != PASSED:
            raise RejectedByHook.from_hook_result(hook_result)

        async with handle_session_exception(
            self.db,
            "destroy_session",
            session_id,
            set_error=True,
        ):

            async with self.db.begin_readonly_session() as db_sess:
                query = (
                    sa.select(SessionRow)
                    .where(SessionRow.id == session_id)
                    .options(selectinload(SessionRow.kernels))
                )
                result = await db_sess.execute(query)
                target_session = result.scalars().first()

            match target_session.status:
                case SessionStatus.PENDING:
                    await SessionRow.set_session_status(
                        self.db, session_id, SessionStatus.CANCELLED
                    )
                case SessionStatus.PULLING:
                    raise GenericForbidden("Cannot destroy sessions in pulling status")
                case SessionStatus.SCHEDULED | SessionStatus.PREPARING | SessionStatus.TERMINATING | SessionStatus.ERROR:
                    if not forced:
                        raise GenericForbidden(
                            "Cannot destroy sessions in scheduled/preparing/terminating/error status",
                        )
                    log.warning(
                        "force-terminating session (s:{}, status:{})",
                        session_id,
                        target_session.status,
                    )
                    await SessionRow.set_session_status(
                        self.db, session_id, SessionStatus.TERMINATING
                    )
                case _:
                    await SessionRow.set_session_status(
                        self.db, session_id, SessionStatus.TERMINATING
                    )

            kernel_list = target_session.kernels
            main_stat = {}
            per_agent_tasks = []
            now = datetime.now(tzutc())
            to_be_terminated = []

            keyfunc = lambda item: item.agent if item.agent is not None else ""
            for agent_id, group_iterator in itertools.groupby(
                sorted(kernel_list, key=keyfunc),
                key=keyfunc,
            ):
                destroyed_kernels = []
                grouped_kernels = [*group_iterator]
                kernel: KernelRow
                for kernel in grouped_kernels:
                    match kernel.status:
                        case KernelStatus.PENDING:

                            async def _update() -> None:
                                async with self.db.begin_session() as db_sess:
                                    await db_sess.execute(
                                        sa.update(KernelRow)
                                        .values(
                                            status=KernelStatus.CANCELLED,
                                            status_info=reason,
                                            status_changed=now,
                                            terminated_at=now,
                                            status_history=sql_json_merge(
                                                KernelRow.status_history,
                                                (),
                                                {
                                                    KernelStatus.CANCELLED.name: now.isoformat(),
                                                },
                                            ),
                                        )
                                        .where(KernelRow.id == kernel.id),
                                    )

                            await execute_with_retry(_update)
                            await self.event_producer.produce_event(
                                KernelCancelledEvent(kernel.id, "", reason),
                            )
                            if kernel.cluster_role == DEFAULT_ROLE:
                                main_stat = {"status": "cancelled"}
                                await self.event_producer.produce_event(
                                    SessionCancelledEvent(
                                        kernel.session_id,
                                        kernel.session_creation_id,
                                        reason,
                                    ),
                                )
                        case KernelStatus.PULLING:
                            raise GenericForbidden("Cannot destroy kernels in pulling status")
                        case KernelStatus.SCHEDULED | KernelStatus.PREPARING | KernelStatus.TERMINATING | KernelStatus.ERROR:
                            if not forced:
                                raise GenericForbidden(
                                    "Cannot destroy kernels in scheduled/preparing/terminating/error status",
                                )
                            log.warning(
                                "force-terminating kernel (k:{}, status:{})",
                                kernel.id,
                                kernel.status,
                            )
                            if kernel.container_id is not None:
                                destroyed_kernels.append(kernel)
                            else:
                                to_be_terminated.append(kernel)

                            async def _update() -> None:
                                kern_stat = await redis_helper.execute(
                                    self.redis_stat,
                                    lambda r: r.get(str(kernel.id)),
                                )
                                async with self.db.begin_session() as db_sess:
                                    values = {
                                        "status": KernelStatus.TERMINATED,
                                        "status_info": reason,
                                        "status_changed": now,
                                        "terminated_at": now,
                                        "status_history": sql_json_merge(
                                            KernelRow.status_history,
                                            (),
                                            {
                                                KernelStatus.TERMINATED.name: now.isoformat(),
                                            },
                                        ),
                                    }
                                    if kern_stat:
                                        values["last_stat"] = msgpack.unpackb(kern_stat)
                                    await db_sess.execute(
                                        sa.update(KernelRow)
                                        .values(**values)
                                        .where(KernelRow.id == kernel.id),
                                    )

                            if kernel.cluster_role == DEFAULT_ROLE:
                                # The main session is terminated;
                                # decrement the user's concurrency counter
                                await redis_helper.execute(
                                    self.redis_stat,
                                    lambda r: r.incrby(
                                        f"keypair.concurrency_used.{kernel.access_key}",
                                        -1,
                                    ),
                                )

                            await execute_with_retry(_update)
                            await self.event_producer.produce_event(
                                KernelTerminatedEvent(kernel.id, reason),
                            )
                        case _:

                            async def _update() -> None:
                                async with self.db.begin_session() as db_sess:
                                    values = {
                                        "status": KernelStatus.TERMINATING,
                                        "status_info": reason,
                                        "status_changed": now,
                                        "status_data": {
                                            "kernel": {"exit_code": None},
                                            "session": {"status": "terminating"},
                                        },
                                        "status_history": sql_json_merge(
                                            KernelRow.status_history,
                                            (),
                                            {
                                                KernelStatus.TERMINATING.name: now.isoformat(),
                                            },
                                        ),
                                    }
                                    await db_sess.execute(
                                        sa.update(KernelRow)
                                        .values(**values)
                                        .where(KernelRow.id == kernel.id),
                                    )

                            if kernel.cluster_role == DEFAULT_ROLE:
                                # The main session is terminated;
                                # decrement the user's concurrency counter
                                await redis_helper.execute(
                                    self.redis_stat,
                                    lambda r: r.incrby(
                                        f"keypair.concurrency_used.{kernel.access_key}",
                                        -1,
                                    ),
                                )

                            await execute_with_retry(_update)
                            await self.event_producer.produce_event(
                                KernelTerminatingEvent(kernel.id, reason),
                            )

                    if kernel.agent_addr is None:
                        await self.mark_kernel_terminated(kernel.id, "missing-agent-allocation")
                        if kernel.cluster_role == DEFAULT_ROLE:
                            main_stat = {"status": "terminated"}
                    else:
                        destroyed_kernels.append(kernel)

                async def _destroy_kernels_in_agent(
                    session: SessionRow, destroyed_kernels: List[KernelRow]
                ) -> None:
                    nonlocal main_stat
                    async with RPCContext(
                        destroyed_kernels[0].agent,
                        destroyed_kernels[0].agent_addr,
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
                                destroyed_kernels[0].agent,
                                session.id,
                            )
                        for kernel in destroyed_kernels:
                            last_stat: Optional[Dict[str, Any]]
                            last_stat = None
                            try:
                                raw_last_stat = await redis_helper.execute(
                                    self.redis_stat, lambda r: r.get(str(kernel.id))
                                )
                                if raw_last_stat is not None:
                                    last_stat = msgpack.unpackb(raw_last_stat)
                                    last_stat["version"] = 2
                            except asyncio.TimeoutError:
                                pass
                            if kernel.cluster_role == DEFAULT_ROLE:
                                main_stat = {
                                    **(last_stat if last_stat is not None else {}),
                                    "status": "terminated",
                                }

                if destroyed_kernels:
                    per_agent_tasks.append(_destroy_kernels_in_agent(session, destroyed_kernels))
                    to_be_terminated.extend(destroyed_kernels)

            if per_agent_tasks:
                await asyncio.gather(*per_agent_tasks, return_exceptions=True)
            for kernel in to_be_terminated:
                await self.event_producer.produce_event(
                    KernelTerminatedEvent(kernel.id, reason),
                )
            await self.hook_plugin_ctx.notify(
                "POST_DESTROY_SESSION",
                (session_id, session.name, session.access_key),
            )
            if forced:
                await self.recalc_resource_usage()
            return main_stat

    async def clean_session(
        self,
        session_id: SessionId,
    ) -> None:
        async def _fetch() -> Row:
            async with self.db.begin_readonly() as conn:
                query = (
                    sa.select(
                        [
                            kernels.c.session_id,
                            kernels.c.cluster_mode,
                            kernels.c.cluster_size,
                            kernels.c.agent,
                            kernels.c.agent_addr,
                            kernels.c.use_host_network,
                        ]
                    )
                    .select_from(kernels)
                    .where(
                        (kernels.c.session_id == session_id)
                        & (kernels.c.cluster_role == DEFAULT_ROLE),
                    )
                )
                result = await conn.execute(query)
                return result.first()

        session = await execute_with_retry(_fetch)
        if session is None:
            return
        if not session["use_host_network"]:
            if session["cluster_mode"] == ClusterMode.SINGLE_NODE and session["cluster_size"] > 1:
                network_name = f'bai-singlenode-{session["session_id"]}'
                try:
                    async with RPCContext(
                        session["agent"],  # the main-container's agent
                        session["agent_addr"],
                        invoke_timeout=None,
                        order_key=session["session_id"],
                        keepalive_timeout=self.rpc_keepalive_timeout,
                    ) as rpc:
                        await rpc.call.destroy_local_network(network_name)
                except Exception:
                    log.exception(f"Failed to destroy the agent-local network {network_name}")
            elif session["cluster_mode"] == ClusterMode.MULTI_NODE:
                network_name = f'bai-multinode-{session["session_id"]}'
                try:
                    try:
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
        session: SessionRow,
    ) -> None:
        log.warning("restart_session({})", session.id)

        async def _restarting_session() -> None:
            async with self.db.begin_session() as db_sess:
                query = (
                    sa.update(SessionRow)
                    .values(
                        status=SessionStatus.RESTARTING,
                        status_history=sql_json_merge(
                            SessionRow.status_history,
                            (),
                            {
                                SessionStatus.RESTARTING.name: datetime.now(tzutc()).isoformat(),
                            },
                        ),
                    )
                    .where(SessionRow.id == session.id)
                )
                await db_sess.execute(query)

        await execute_with_retry(_restarting_session)

        kernel_list = session.kernels

        async def _restart_kernel(kernel: KernelRow) -> None:
            loop = asyncio.get_running_loop()
            try:
                kernel_creation_id = secrets.token_urlsafe(16)
                start_future = loop.create_future()
                self.kernel_creation_tracker[kernel.id] = start_future
                try:
                    async with RPCContext(
                        kernel.agent,  # the main-container's agent
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

                    async def _update_kernel() -> None:
                        async with self.db.begin_session() as db_sess:
                            query = (
                                sa.update(KernelRow)
                                .values(
                                    status=KernelStatus.RUNNING,
                                    container_id=kernel_info["container_id"],
                                    repl_in_port=kernel_info["repl_in_port"],
                                    repl_out_port=kernel_info["repl_out_port"],
                                    stdin_port=kernel_info["stdin_port"],
                                    stdout_port=kernel_info["stdout_port"],
                                    service_ports=kernel_info.get("service_ports", []),
                                    status_history=sql_json_merge(
                                        KernelRow.status_history,
                                        (),
                                        {
                                            KernelStatus.RUNNING.name: datetime.now(
                                                tzutc()
                                            ).isoformat(),
                                        },
                                    ),
                                )
                                .where(KernelRow.id == kernel.id)
                            )
                            await db_sess.execute(query)

                    await execute_with_retry(_update_kernel)
                finally:
                    del self.kernel_creation_tracker[kernel.id]
            except Exception:
                log.exception("unexpected-error in _restart_kerenl()")

        restart_coros = []
        for kernel in kernel_list:
            restart_coros.append(_restart_kernel(kernel))
        async with handle_session_exception(
            self.db,
            "restart_session",
            session.id,
            set_error=True,
        ):
            await asyncio.gather(*restart_coros)

        async def _update_session() -> None:
            async with self.db.begin_session() as db_sess:
                query = (
                    sa.update(SessionRow)
                    .values(
                        status=SessionStatus.RUNNING,
                        status_history=sql_json_merge(
                            SessionRow.status_history,
                            (),
                            {
                                SessionStatus.RUNNING.name: datetime.now(tzutc()).isoformat(),
                            },
                        ),
                    )
                    .where(SessionRow.id == session.id)
                )
                await db_sess.execute(query)

        await execute_with_retry(_update_session)

        # NOTE: If the restarted session is a batch-type one, then the startup command
        #       will be executed again after restart.
        await self.event_producer.produce_event(
            SessionStartedEvent(session.id, session.creation_id),
        )

    async def execute(
        self,
        session: SessionRow,
        api_version: Tuple[int, str],
        run_id: str,
        mode: str,
        code: str,
        opts: Mapping[str, Any],
        *,
        flush_timeout: float = None,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            # The agent aggregates at most 2 seconds of outputs
            # if the kernel runs for a long time.
            major_api_version = api_version[0]
            if major_api_version == 4:  # manager-agent protocol is same.
                major_api_version = 3
            async with RPCContext(
                session.main_kernel.agent,
                session.main_kernel.agent_addr,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.execute(
                    str(session.main_kernel.id),
                    major_api_version,
                    run_id,
                    mode,
                    code,
                    opts,
                    flush_timeout,
                )

    async def interrupt_session(
        self,
        session: SessionRow,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            async with RPCContext(
                session.main_kernel.agent,
                session.main_kernel.agent_addr,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.interrupt_kernel(str(session.main_kernel.id))

    async def get_completions(
        self,
        session: SessionRow,
        text: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            async with RPCContext(
                session.main_kernel.agent,
                session.main_kernel.agent_addr,
                invoke_timeout=10,
                order_key=session.main_kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.get_completions(str(session.main_kernel.id), text, opts)

    async def start_service(
        self,
        session: SessionRow,
        service: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            async with RPCContext(
                session.main_kernel.agent,
                session.main_kernel.agent_addr,
                invoke_timeout=None,
                order_key=session.main_kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.start_service(str(session.main_kernel.id), service, opts)

    async def shutdown_service(
        self,
        session: SessionRow,
        service: str,
    ) -> None:
        async with handle_session_exception(self.db, "shutdown_service", session.id):
            async with RPCContext(
                session.main_kernel.agent,
                session.main_kernel.agent_addr,
                invoke_timeout=None,
                order_key=session.main_kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.shutdown_service(str(session.main_kernel.id), service)

    async def upload_file(
        self,
        session: SessionRow,
        filename: str,
        payload: bytes,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "upload_file", session.id):
            async with RPCContext(
                session.main_kernel.agent,
                session.main_kernel.agent_addr,
                invoke_timeout=None,
                order_key=session.main_kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.upload_file(str(session.main_kernel.id), filename, payload)

    async def download_file(
        self,
        session: SessionRow,
        access_key: AccessKey,
        filepath: str,
    ) -> bytes:
        kernel = session.main_kernel
        async with handle_session_exception(
            self.db, "download_file", kernel.session_id, access_key
        ):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=None,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.download_file(str(kernel.id), filepath)

    async def download_single(
        self,
        session: SessionRow,
        access_key: AccessKey,
        filepath: str,
    ) -> bytes:
        kernel = session.main_kernel
        async with handle_session_exception(
            self.db, "download_single", kernel.session_id, access_key
        ):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=None,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.download_single(str(kernel.id), filepath)

    async def list_files(
        self,
        session: SessionRow,
        path: str,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "list_files", session.id):
            async with RPCContext(
                session.main_kernel.agent,
                session.main_kernel.agent_addr,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.list_files(str(session.main_kernel.id), path)

    async def get_logs_from_agent(
        self,
        session: SessionRow,
    ) -> str:
        async with handle_session_exception(self.db, "get_logs_from_agent", session.id):
            async with RPCContext(
                session.main_kernel.agent,
                session.main_kernel.agent_addr,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                reply = await rpc.call.get_logs(str(session.main_kernel.id))
                return reply["logs"]

    async def increment_session_usage(
        self,
        session: SessionRow,
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
            coro = rpc.call.clean_all_kernels("manager-freeze-force-kill")
            return await coro

    async def kill_all_sessions(self, conn=None):
        async with reenter_txn(self.db, conn, {"postgresql_readonly": True}) as conn:
            query = sa.select([agents.c.id, agents.c.addr]).where(
                agents.c.status == AgentStatus.ALIVE
            )
            result = await conn.execute(query)
            rows = result.fetchall()
        tasks = []
        for row in rows:
            tasks.append(
                self.kill_all_sessions_in_agent(row["id"], row["addr"]),
            )
        await asyncio.gather(*tasks, return_exceptions=True)

    async def handle_heartbeat(self, agent_id, agent_info):
        now = datetime.now(tzutc())
        slot_key_and_units = {
            SlotName(k): SlotTypes(v[0]) for k, v in agent_info["resource_slots"].items()
        }
        available_slots = ResourceSlot(
            {SlotName(k): Decimal(v[1]) for k, v in agent_info["resource_slots"].items()}
        )
        current_addr = agent_info["addr"]
        sgroup = agent_info.get("scaling_group", "default")
        async with self.heartbeat_lock:

            instance_rejoin = False

            # Update "last seen" timestamp for liveness tracking
            await redis_helper.execute(
                self.redis_live,
                lambda r: r.hset("agent.last_seen", agent_id, now.timestamp()),
            )

            # Check and update status of the agent record in DB
            async def _update() -> None:
                nonlocal instance_rejoin
                async with self.db.begin() as conn:
                    fetch_query = (
                        sa.select(
                            [
                                agents.c.status,
                                agents.c.addr,
                                agents.c.scaling_group,
                                agents.c.available_slots,
                                agents.c.version,
                                agents.c.compute_plugins,
                                agents.c.architecture,
                            ]
                        )
                        .select_from(agents)
                        .where(agents.c.id == agent_id)
                        .with_for_update()
                    )
                    result = await conn.execute(fetch_query)
                    row = result.first()

                    if row is None or row["status"] is None:
                        # new agent detected!
                        log.info("agent {0} joined!", agent_id)
                        await self.shared_config.update_resource_slots(slot_key_and_units)
                        insert_query = sa.insert(agents).values(
                            {
                                "id": agent_id,
                                "status": AgentStatus.ALIVE,
                                "region": agent_info["region"],
                                "scaling_group": sgroup,
                                "available_slots": available_slots,
                                "occupied_slots": {},
                                "addr": agent_info["addr"],
                                "first_contact": now,
                                "lost_at": sa.null(),
                                "version": agent_info["version"],
                                "compute_plugins": agent_info["compute_plugins"],
                                "architecture": agent_info.get("architecture", "x86_64"),
                            }
                        )
                        result = await conn.execute(insert_query)
                        assert result.rowcount == 1
                    elif row["status"] == AgentStatus.ALIVE:
                        updates = {}
                        if row["available_slots"] != available_slots:
                            updates["available_slots"] = available_slots
                        if row["scaling_group"] != sgroup:
                            updates["scaling_group"] = sgroup
                        if row["addr"] != current_addr:
                            updates["addr"] = current_addr
                        if row["version"] != agent_info["version"]:
                            updates["version"] = agent_info["version"]
                        if row["compute_plugins"] != agent_info["compute_plugins"]:
                            updates["compute_plugins"] = agent_info["compute_plugins"]
                        if row["architecture"] != agent_info["architecture"]:
                            updates["architecture"] = agent_info["architecture"]
                        # occupied_slots are updated when kernels starts/terminates
                        if updates:
                            await self.shared_config.update_resource_slots(slot_key_and_units)
                            update_query = (
                                sa.update(agents).values(updates).where(agents.c.id == agent_id)
                            )
                            await conn.execute(update_query)
                    elif row["status"] in (AgentStatus.LOST, AgentStatus.TERMINATED):
                        await self.shared_config.update_resource_slots(slot_key_and_units)
                        instance_rejoin = True
                        update_query = (
                            sa.update(agents)
                            .values(
                                {
                                    "status": AgentStatus.ALIVE,
                                    "region": agent_info["region"],
                                    "scaling_group": sgroup,
                                    "addr": agent_info["addr"],
                                    "lost_at": sa.null(),
                                    "available_slots": available_slots,
                                    "version": agent_info["version"],
                                    "compute_plugins": agent_info["compute_plugins"],
                                    "architecture": agent_info["architecture"],
                                }
                            )
                            .where(agents.c.id == agent_id)
                        )
                        await conn.execute(update_query)
                    else:
                        log.error("should not reach here! {0}", type(row["status"]))

            try:
                await execute_with_retry(_update)
            except sa.exc.IntegrityError:
                log.error("Scaling group named [{}] does not exist.", sgroup)
                return

            if instance_rejoin:
                await self.event_producer.produce_event(
                    AgentStartedEvent("revived"),
                    source=agent_id,
                )

            # Update the mapping of kernel images to agents.
            known_registries = await get_known_registries(self.shared_config.etcd)
            loaded_images = msgpack.unpackb(zlib.decompress(agent_info["images"]))

            async def _pipe_builder(r: Redis):
                pipe = r.pipeline()
                for image in loaded_images:
                    image_ref = ImageRef(image[0], known_registries, agent_info["architecture"])
                    await pipe.sadd(image_ref.canonical, agent_id)
                return pipe

            await redis_helper.execute(self.redis_image, _pipe_builder)

        await self.hook_plugin_ctx.notify(
            "POST_AGENT_HEARTBEAT",
            (agent_id, sgroup, available_slots),
        )

    async def mark_agent_terminated(self, agent_id: AgentId, status: AgentStatus) -> None:
        await redis_helper.execute(self.redis_live, lambda r: r.hdel("agent.last_seen", agent_id))

        async def _pipe_builder(r: Redis):
            pipe = r.pipeline()
            async for imgname in r.scan_iter():
                await pipe.srem(imgname, agent_id)
            return pipe

        async def _update() -> None:
            async with self.db.begin() as conn:
                fetch_query = (
                    sa.select(
                        [
                            agents.c.status,
                            agents.c.addr,
                        ]
                    )
                    .select_from(agents)
                    .where(agents.c.id == agent_id)
                    .with_for_update()
                )
                result = await conn.execute(fetch_query)
                row = result.first()
                prev_status = row["status"]
                if prev_status in (None, AgentStatus.LOST, AgentStatus.TERMINATED):
                    return

                if status == AgentStatus.LOST:
                    log.warning("agent {0} heartbeat timeout detected.", agent_id)
                elif status == AgentStatus.TERMINATED:
                    log.info("agent {0} has terminated.", agent_id)
                now = datetime.now(tzutc())
                update_query = (
                    sa.update(agents)
                    .values(
                        {
                            "status": status,
                            "status_changed": now,
                            "lost_at": now,
                        }
                    )
                    .where(agents.c.id == agent_id)
                )
                await conn.execute(update_query)

        await redis_helper.execute(self.redis_image, _pipe_builder)
        await execute_with_retry(_update)

    async def sync_kernel_stats(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> None:
        per_kernel_updates = {}
        log.debug("sync_kernel_stats(k:{!r})", kernel_ids)
        for kernel_id in kernel_ids:
            raw_kernel_id = str(kernel_id)
            kern_stat = await redis_helper.execute(
                self.redis_stat,
                lambda r: r.get(raw_kernel_id),
            )
            if kern_stat is None:
                log.warning("sync_kernel_stats(k:{}): no statistics updates", kernel_id)
                continue
            else:
                per_kernel_updates[kernel_id] = msgpack.unpackb(kern_stat)

        async def _update():
            async with self.db.begin() as conn:
                update_query = (
                    sa.update(kernels)
                    .where(kernels.c.id == sa.bindparam("kernel_id"))
                    .values({kernels.c.last_stat: sa.bindparam("last_stat")})
                )
                params = []
                for kernel_id, updates in per_kernel_updates.items():
                    params.append(
                        {
                            "kernel_id": kernel_id,
                            "last_stat": updates,
                        }
                    )
                await conn.execute(update_query, params)

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

        kern_stat = await redis_helper.execute(
            self.redis_stat,
            lambda r: r.get(str(kernel_id)),
        )

        async def _update_kernel_status() -> Tuple[SessionId, AccessKey, AgentId] | None:
            async with self.db.begin_session() as db_sess:
                # Check the current status.
                select_query = (
                    sa.select(
                        KernelRow.access_key,
                        KernelRow.agent,
                        KernelRow.status,
                        KernelRow.occupied_slots,
                        KernelRow.session_id,
                    )
                    .where(KernelRow.id == kernel_id)
                    .with_for_update()
                )
                result = await db_sess.execute(select_query)
                kernel = result.first()
                if kernel is None or kernel.status in (
                    KernelStatus.CANCELLED,
                    KernelStatus.TERMINATED,
                    KernelStatus.RESTARTING,
                ):
                    # Skip if non-existent, already terminated, or restarting.
                    return None

                session_id, access_key, agent = kernel.session_id, kernel.access_key, kernel.agent
                # Change the status to TERMINATED.
                # (we don't delete the row for later logging and billing)
                now = datetime.now(tzutc())
                values = {
                    "status": KernelStatus.TERMINATED,
                    "status_info": reason,
                    "status_changed": now,
                    "status_data": sql_json_merge(
                        KernelRow.status_data,
                        ("kernel",),
                        {"exit_code": exit_code},
                    ),
                    "status_history": sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {
                            KernelStatus.TERMINATED.name: now.isoformat(),
                        },
                    ),
                    "terminated_at": now,
                }
                if kern_stat:
                    values["last_stat"] = msgpack.unpackb(kern_stat)
                update_query = (
                    sa.update(KernelRow).values(**values).where(KernelRow.id == kernel_id)
                )
                await db_sess.execute(update_query)
                return session_id, access_key, agent

        result = await execute_with_retry(_update_kernel_status)
        if result is None:
            return

        assert result is not None
        session_id, access_key, agent = result

        async def _check_session() -> None:
            async with self.db.begin_session() as db_sess:
                query = (
                    sa.select(SessionRow)
                    .where(SessionRow.id == session_id)
                    .options(selectinload(SessionRow.kernels))
                )
                result = await db_sess.execute(query)
                session: SessionRow = result.scalars().first()
                candidate_status = determine_session_status(session.kernels)
                if candidate_status in SESSION_STATUS_TRANSITION_MAP[session.status]:
                    now = datetime.now(tzutc())
                    update_query = (
                        sa.update(SessionRow)
                        .where(SessionRow.id == session_id)
                        .values(
                            status=candidate_status,
                            terminated_at=now,
                            status_history=sql_json_merge(
                                SessionRow.status_history,
                                (),
                                {
                                    SessionStatus.TERMINATED.name: datetime.now(
                                        tzutc()
                                    ).isoformat(),
                                },
                            ),
                        )
                    )
                    await db_sess.execute(update_query)

        await execute_with_retry(_check_session)

        async def _recalc() -> None:
            async with self.db.begin() as conn:
                log.debug(
                    "recalculate concurrency used in kernel termination (ak: {})",
                    access_key,
                )
                await recalc_concurrency_used(conn, self.redis_stat, access_key)
                log.debug(
                    "recalculate agent resource occupancy in kernel termination (agent: {})",
                    agent,
                )
                await recalc_agent_resource_occupancy(conn, agent)

        await execute_with_retry(_recalc)

        # Perform statistics sync in a separate transaction block, since
        # it may take a while to fetch stats from Redis.

        await self.sync_kernel_stats([kernel_id])

    async def check_session_terminated(
        self,
        kernel_id: KernelId,
        reason: str,
    ) -> None:
        async def _check_and_mark() -> Tuple[bool, SessionId]:
            async with self.db.begin_session() as db_sess:
                kernel_query = sa.select(KernelRow.session_id).where(KernelRow.id == kernel_id)
                session_id = (await db_sess.execute(kernel_query)).scalar()
                session = await SessionRow.get_session_with_kernels(
                    session_id, allow_stale=True, db_session=db_sess
                )
                sibling_kernels = session.kernels
                sess_status = determine_session_status(sibling_kernels)
                now = datetime.now(tzutc())
                if sess_status in SESSION_STATUS_TRANSITION_MAP[session.status]:
                    values = {
                        "status": sess_status,
                        "status_info": reason,
                        "terminated_at": now,
                        "status_history": sql_json_merge(
                            SessionRow.status_history,
                            (),
                            {
                                sess_status.name: datetime.now(tzutc()).isoformat(),
                            },
                        ),
                    }
                    query = (
                        sa.update(SessionRow).values(**values).where(SessionRow.id == session_id)
                    )
                    await db_sess.execute(query)
                all_terminated = session.status in (
                    SessionStatus.TERMINATED,
                    SessionStatus.CANCELLED,
                )
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

    async def _get_user_email(
        self,
        kernel: KernelRow,
    ) -> str:
        async with self.db.begin_readonly() as db_conn:
            query = sa.select(UserRow.email).where(UserRow.uuid == kernel.user_uuid)
            result = await db_conn.execute(query)
            user_email = str(result.scalar())
            user_email = user_email.replace("@", "_")
        return user_email

    async def get_commit_status(
        self,
        session: SessionRow,
    ) -> Mapping[str, str]:
        kernel: KernelRow = session.main_kernel
        if kernel.status != KernelStatus.RUNNING:
            return {"status": "", "kernel": str(kernel.id)}
        email = await self._get_user_email(kernel)
        async with handle_session_exception(self.db, "commit_session", session.id):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=None,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                return await rpc.call.get_commit_status(str(kernel.id), email)

    async def commit_session(
        self,
        session: SessionRow,
        filename: str | None,
    ) -> Mapping[str, Any]:
        """
        Commit a main kernel's container of the given session.
        """

        kernel: KernelRow = session.main_kernel
        if kernel.status != KernelStatus.RUNNING:
            raise InvalidAPIParameters(
                f"Unable to commit since kernel(id: {kernel.id}) of session(id: {session.id}) is currently not RUNNING."
            )
        email = await self._get_user_email(kernel)
        now = datetime.now(tzutc()).strftime("%Y-%m-%dT%HH%MM%SS")
        shortend_sname = session.name[:SESSION_NAME_LEN_LIMIT]
        registry, _, filtered = kernel.image.partition("/")
        img_path, _, image_name = filtered.partition("/")
        filename = f"{now}_{shortend_sname}_{image_name}.tar.gz"
        filename = filename.replace(":", "-")
        async with handle_session_exception(self.db, "commit_session", session.id):
            async with RPCContext(
                kernel.agent,
                kernel.agent_addr,
                invoke_timeout=None,
                order_key=kernel.id,
                keepalive_timeout=self.rpc_keepalive_timeout,
            ) as rpc:
                resp: Mapping[str, Any] = await rpc.call.commit(str(kernel.id), email, filename)
        return resp

    async def get_agent_local_config(
        self,
        agent_id: AgentId,
        agent_addr: str,
    ) -> Mapping[str, str]:
        async with RPCContext(
            agent_id,
            agent_addr,
            invoke_timeout=None,
        ) as rpc:
            return await rpc.call.get_local_config()

    async def get_abusing_report(
        self,
        kernel_id: KernelId,
        agent_id: AgentId,
        agent_addr: str,
    ) -> Optional[Mapping[str, str]]:
        async with RPCContext(
            agent_id,
            agent_addr,
            invoke_timeout=None,
        ) as rpc:
            return await rpc.call.get_abusing_report(str(kernel_id))


async def check_scaling_group(
    conn: SAConnection,
    scaling_group: str | None,
    session_type: SessionTypes,
    access_key: AccessKey,
    domain_name: str,
    group_id: Union[uuid.UUID, str],
) -> str:
    # Check scaling group availability if scaling_group parameter is given.
    # If scaling_group is not provided, it will be selected as the first one among
    # the list of allowed scaling groups.
    candidates = await query_allowed_sgroups(
        conn,
        domain_name,
        group_id,
        access_key,
    )
    if not candidates:
        raise ScalingGroupNotFound("You have no scaling groups allowed to use.")

    stype = session_type.value.lower()
    if scaling_group is None:
        for sgroup in candidates:
            allowed_session_types = sgroup["scheduler_opts"].allowed_session_types
            if stype in allowed_session_types:
                scaling_group = sgroup["name"]
                break
        else:
            raise ScalingGroupNotFound(
                f"No scaling groups accept the session type '{session_type}'.",
            )
    else:
        err_msg = (
            f"The scaling group '{scaling_group}' does not exist "
            f"or you do not have access to the scaling group '{scaling_group}'."
        )
        for sgroup in candidates:
            if scaling_group == sgroup["name"]:
                # scaling_group's unique key is 'name' field for now,
                # but we will change scaling_group's unique key to new 'id' field.
                allowed_session_types = sgroup["scheduler_opts"].allowed_session_types
                if stype in allowed_session_types:
                    break
                err_msg = (
                    f"The scaling group '{scaling_group}' does not accept "
                    f"the session type '{session_type}'. "
                )
        else:
            raise ScalingGroupNotFound(err_msg)
    assert scaling_group is not None
    return scaling_group
