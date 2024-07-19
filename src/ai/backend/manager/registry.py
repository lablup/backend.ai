from __future__ import annotations

import asyncio
import base64
import copy
import itertools
import logging
import re
import secrets
import time
import typing
import uuid
import zlib
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
    TypeAlias,
    Union,
    cast,
)
from urllib.parse import urlparse

import aiodocker
import aiohttp
import aiotools
import sqlalchemy as sa
import yarl
from async_timeout import timeout as _timeout
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dateutil.parser import isoparse
from dateutil.tz import tzutc
from redis.asyncio import Redis
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload, selectinload, with_loader_criteria
from sqlalchemy.orm.exc import NoResultFound
from yarl import URL

from ai.backend.common import msgpack, redis_helper
from ai.backend.common.asyncio import cancel_tasks
from ai.backend.common.docker import ImageRef, get_known_registries, get_registry_info
from ai.backend.common.events import (
    AgentHeartbeatEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
    DoAgentResourceCheckEvent,
    DoSyncKernelLogsEvent,
    DoTerminateSessionEvent,
    KernelCancelledEvent,
    KernelCreatingEvent,
    KernelLifecycleEventReason,
    KernelPreparingEvent,
    KernelPullingEvent,
    KernelStartedEvent,
    KernelTerminatedEvent,
    KernelTerminatingEvent,
    ModelServiceStatusEvent,
    RouteCreatedEvent,
    SessionCancelledEvent,
    SessionEnqueuedEvent,
    SessionFailureEvent,
    SessionPreparingEvent,
    SessionScheduledEvent,
    SessionStartedEvent,
    SessionSuccessEvent,
    SessionTerminatedEvent,
    SessionTerminatingEvent,
)
from ai.backend.common.exception import AliasResolutionFailed
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext
from ai.backend.common.service_ports import parse_service_ports
from ai.backend.common.types import (
    AbuseReport,
    AccessKey,
    AgentId,
    BinarySize,
    ClusterInfo,
    ClusterMode,
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
    CommitStatus,
    DeviceId,
    HardwareMetadata,
    ImageAlias,
    ImageRegistry,
    KernelEnqueueingConfig,
    KernelId,
    ModelServiceStatus,
    RedisConnectionInfo,
    ResourceSlot,
    SessionEnqueueingConfig,
    SessionId,
    SessionTypes,
    SlotName,
    SlotTypes,
    check_typed_dict,
)
from ai.backend.common.utils import str_to_timedelta
from ai.backend.manager.utils import query_userinfo

from .api.exceptions import (
    BackendError,
    GenericForbidden,
    ImageNotFound,
    InstanceNotFound,
    InvalidAPIParameters,
    QuotaExceeded,
    RejectedByHook,
    ScalingGroupNotFound,
    SessionAlreadyExists,
    SessionNotFound,
    TooManySessionsMatched,
)
from .config import LocalConfig, SharedConfig
from .defs import DEFAULT_IMAGE_ARCH, DEFAULT_ROLE, INTRINSIC_SLOTS
from .exceptions import MultiAgentError, convert_to_status_data
from .models import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
    PRIVATE_KERNEL_ROLES,
    USER_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    USER_RESOURCE_OCCUPYING_SESSION_STATUSES,
    AgentRow,
    AgentStatus,
    EndpointLifecycle,
    EndpointRow,
    ImageRow,
    KernelLoadingStrategy,
    KernelRole,
    KernelRow,
    KernelStatus,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    RouteStatus,
    RoutingRow,
    SessionDependencyRow,
    SessionRow,
    SessionStatus,
    UserRole,
    UserRow,
    agents,
    domains,
    handle_session_exception,
    kernels,
    prepare_dotfiles,
    prepare_vfolder_mounts,
    query_allowed_sgroups,
    query_bootstrap_script,
    recalc_agent_resource_occupancy,
    recalc_concurrency_used,
    scaling_groups,
    verify_vfolder_name,
)
from .models.session import (
    COMPUTE_CONCURRENCY_USED_KEY_PREFIX,
    SESSION_KERNEL_STATUS_MAPPING,
    SYSTEM_CONCURRENCY_USED_KEY_PREFIX,
    ConcurrencyUsed,
)
from .models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
    is_db_retry_error,
    reenter_txn,
    reenter_txn_session,
    sql_json_merge,
)
from .types import UserScope

if TYPE_CHECKING:
    from sqlalchemy.engine.row import Row
    from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection

    from ai.backend.common.auth import PublicKey, SecretKey
    from ai.backend.common.events import EventDispatcher, EventProducer

    from .agent_cache import AgentRPCCache
    from .models.storage import StorageSessionManager
    from .scheduler.types import AgentAllocationContext, KernelAgentBinding, SchedulingContext

MSetType: TypeAlias = Mapping[Union[str, bytes], Union[bytes, float, int, str]]
__all__ = ["AgentRegistry", "InstanceNotFound"]

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

SESSION_NAME_LEN_LIMIT = 10


class AgentRegistry:
    """
    Provide a high-level API to create, destroy, and query the computation
    kernels.

    The registry is also responsible to implement our resource management
    policy, such as the limitation of maximum number of kernels per instance.
    """

    _kernel_actual_allocated_resources: dict[KernelId, ResourceSlot]

    local_config: LocalConfig
    session_creation_tracker: dict[str, asyncio.Event]
    pending_waits: set[asyncio.Task[None]]
    database_ptask_group: aiotools.PersistentTaskGroup
    webhook_ptask_group: aiotools.PersistentTaskGroup

    def __init__(
        self,
        local_config: LocalConfig,
        shared_config: SharedConfig,
        db: ExtendedAsyncSAEngine,
        agent_cache: AgentRPCCache,
        redis_stat: RedisConnectionInfo,
        redis_live: RedisConnectionInfo,
        redis_image: RedisConnectionInfo,
        redis_stream: RedisConnectionInfo,
        event_dispatcher: EventDispatcher,
        event_producer: EventProducer,
        storage_manager: StorageSessionManager,
        hook_plugin_ctx: HookPluginContext,
        *,
        debug: bool = False,
        manager_public_key: PublicKey,
        manager_secret_key: SecretKey,
    ) -> None:
        self.local_config = local_config
        self.shared_config = shared_config
        self.docker = aiodocker.Docker()
        self.db = db
        self.agent_cache = agent_cache
        self.redis_stat = redis_stat
        self.redis_live = redis_live
        self.redis_image = redis_image
        self.redis_stream = redis_stream
        self.event_dispatcher = event_dispatcher
        self.event_producer = event_producer
        self.storage_manager = storage_manager
        self.hook_plugin_ctx = hook_plugin_ctx
        self._kernel_actual_allocated_resources = {}
        self.debug = debug
        self.rpc_keepalive_timeout = int(
            shared_config.get("config/network/rpc/keepalive-timeout", "60")
        )
        self.rpc_auth_manager_public_key = manager_public_key
        self.rpc_auth_manager_secret_key = manager_secret_key

    async def init(self) -> None:
        self.heartbeat_lock = asyncio.Lock()
        self.session_creation_tracker = {}
        self.pending_waits = set()
        self.database_ptask_group = aiotools.PersistentTaskGroup()
        self.webhook_ptask_group = aiotools.PersistentTaskGroup()

        # passive events
        evd = self.event_dispatcher
        evd.consume(
            KernelPreparingEvent, self, handle_kernel_creation_lifecycle, name="api.session.kprep"
        )
        evd.consume(
            KernelPullingEvent, self, handle_kernel_creation_lifecycle, name="api.session.kpull"
        )
        evd.consume(
            KernelCreatingEvent, self, handle_kernel_creation_lifecycle, name="api.session.kcreat"
        )
        evd.consume(
            KernelStartedEvent, self, handle_kernel_creation_lifecycle, name="api.session.kstart"
        )
        evd.consume(
            KernelCancelledEvent, self, handle_kernel_creation_lifecycle, name="api.session.kstart"
        )
        evd.subscribe(
            SessionStartedEvent,
            self,
            handle_session_creation_lifecycle,
            name="api.session.sstart",
        )
        evd.subscribe(
            SessionCancelledEvent,
            self,
            handle_session_creation_lifecycle,
            name="api.session.scancel",
        )
        evd.consume(
            KernelTerminatingEvent,
            self,
            handle_kernel_termination_lifecycle,
            name="api.session.kterming",
        )
        evd.consume(
            KernelTerminatedEvent,
            self,
            handle_kernel_termination_lifecycle,
            name="api.session.kterm",
        )
        evd.consume(
            ModelServiceStatusEvent,
            self,
            handle_model_service_status_update,
        )
        evd.consume(
            SessionTerminatingEvent,
            self,
            handle_session_termination_lifecycle,
            name="api.session.sterming",
        )
        evd.consume(
            SessionTerminatedEvent,
            self,
            handle_session_termination_lifecycle,
            name="api.session.sterm",
        )
        evd.consume(SessionEnqueuedEvent, self, invoke_session_callback)
        evd.consume(SessionScheduledEvent, self, invoke_session_callback)
        evd.consume(SessionPreparingEvent, self, invoke_session_callback)
        evd.consume(SessionSuccessEvent, self, handle_batch_result)
        evd.consume(SessionFailureEvent, self, handle_batch_result)
        evd.consume(AgentStartedEvent, self, handle_agent_lifecycle)
        evd.consume(AgentTerminatedEvent, self, handle_agent_lifecycle)
        evd.consume(AgentHeartbeatEvent, self, handle_agent_heartbeat)
        evd.consume(RouteCreatedEvent, self, handle_route_creation)

        # action-trigerring events
        evd.consume(DoSyncKernelLogsEvent, self, handle_kernel_log, name="api.session.syncklog")
        evd.consume(
            DoTerminateSessionEvent, self, handle_destroy_session, name="api.session.doterm"
        )
        evd.consume(DoAgentResourceCheckEvent, self, handle_check_agent_resource)

    async def shutdown(self) -> None:
        await cancel_tasks(self.pending_waits)
        await self.database_ptask_group.shutdown()
        await self.webhook_ptask_group.shutdown()

    async def get_instance(self, inst_id: AgentId, field=None):
        async with self.db.begin_readonly() as conn:
            cols = [agents.c.id, agents.c.public_key]
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
            async for row in await conn.stream(query):
                yield row

    async def update_instance(self, inst_id, updated_fields):
        async def _update() -> None:
            async with self.db.begin() as conn:
                query = sa.update(agents).values(**updated_fields).where(agents.c.id == inst_id)
                await conn.execute(query)

        await execute_with_retry(_update)

    async def gather_agent_hwinfo(self, instance_id: AgentId) -> Mapping[str, HardwareMetadata]:
        agent = await self.get_instance(instance_id, agents.c.addr)
        async with self.agent_cache.rpc_context(agent["id"]) as rpc:
            result = await rpc.call.gather_hwinfo()
            return {k: check_typed_dict(v, HardwareMetadata) for k, v in result.items()}

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
                HardwareMetadata,
            )

    async def create_session(
        self,
        session_name: str,
        image: str,
        architecture: str,
        user_scope: UserScope,
        owner_access_key: AccessKey,
        resource_policy: dict,
        session_type: SessionTypes,
        config: dict[str, Any],
        cluster_mode: ClusterMode,
        cluster_size: int,
        dry_run=False,
        reuse=False,
        enqueue_only=False,
        max_wait_seconds=0,
        bootstrap_script: Optional[str] = None,
        dependencies: Optional[List[uuid.UUID]] = None,
        startup_command: Optional[str] = None,
        starts_at_timestamp: Optional[str] = None,
        tag: Optional[str] = None,
        callback_url: Optional[yarl.URL] = None,
        route_id: Optional[uuid.UUID] = None,
        sudo_session_enabled: bool = False,
    ) -> Mapping[str, Any]:
        log.debug("create_session():")
        resp: MutableMapping[str, Any] = {}

        current_task = asyncio.current_task()
        assert current_task is not None

        # Check work directory and reserved name directory.
        mount_map = config.get("mount_map")

        if mount_map is not None:
            original_folders = mount_map.keys()
            alias_folders = mount_map.values()
            if len(alias_folders) != len(set(alias_folders)):
                raise InvalidAPIParameters("Duplicate alias folder name exists.")

            alias_name: str
            for alias_name in alias_folders:
                if alias_name is None:
                    continue
                if alias_name.startswith("/home/work/"):
                    alias_name = alias_name.replace("/home/work/", "")
                if alias_name == "":
                    raise InvalidAPIParameters("Alias name cannot be empty.")
                if not verify_vfolder_name(alias_name):
                    raise InvalidAPIParameters(str(alias_name) + " is reserved for internal path.")
                if alias_name in original_folders:
                    raise InvalidAPIParameters(
                        "Alias name cannot be set to an existing folder name: " + str(alias_name)
                    )

        if _resources := config["resources"]:
            available_resource_slots = await self.shared_config.get_resource_slots()
            try:
                ResourceSlot.from_user_input(_resources, available_resource_slots)
            except ValueError as e:
                raise InvalidAPIParameters(f"Invalid resource allocation: {e}")

        # Resolve the image reference.
        try:
            async with self.db.begin_readonly_session() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [
                        ImageRef(image, ["*"], architecture),
                        ImageAlias(image),
                    ],
                )
            requested_image_ref = image_row.image_ref
            if (
                _owner_id := image_row.labels.get("ai.backend.customized-image.owner")
            ) and _owner_id != f"user:{user_scope.user_uuid}":
                raise ImageNotFound
            if not requested_image_ref.is_local:
                async with self.db.begin_readonly() as conn:
                    query = (
                        sa.select([domains.c.allowed_docker_registries])
                        .select_from(domains)
                        .where(domains.c.name == user_scope.domain_name)
                    )
                    allowed_registries = await conn.scalar(query)
                    if requested_image_ref.registry not in allowed_registries:
                        raise AliasResolutionFailed
        except AliasResolutionFailed:
            raise ImageNotFound("unknown alias or disallowed registry")

        # Check existing (access_key, session_name) instance
        try:
            # NOTE: We can reuse the session IDs of TERMINATED sessions only.
            # NOTE: Reusing a session in the PENDING status returns an empty value in service_ports.
            async with self.db.begin_readonly_session() as db_sess:
                sess = await SessionRow.get_session(
                    db_sess,
                    session_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )
            running_image_ref = ImageRef(
                sess.main_kernel.image, [sess.main_kernel.registry], sess.main_kernel.architecture
            )
            if running_image_ref != requested_image_ref:
                # The image must be same if get_or_create() called multiple times
                # against an existing (non-terminated) session
                raise SessionAlreadyExists(extra_data={"existingSessionId": str(sess.id)})
            if not reuse:
                # Respond as error since the client did not request to reuse,
                # but provide the overlapping session ID for later use.
                raise SessionAlreadyExists(extra_data={"existingSessionId": str(sess.id)})
            # Respond as success with the reused session's information.
            return {
                "sessionId": str(sess.id),
                "sessionName": str(sess.name),
                "status": sess.status.name,
                "service_ports": sess.main_kernel.service_ports,
                "created": False,
            }
        except SessionNotFound:
            # It's time to create a new session.
            pass

        if session_type == SessionTypes.BATCH and not startup_command:
            raise InvalidAPIParameters("Batch sessions must have a non-empty startup command.")
        if session_type != SessionTypes.BATCH and starts_at_timestamp:
            raise InvalidAPIParameters("Parameter starts_at should be used only for batch sessions")
        starts_at: Union[datetime, None] = None
        if starts_at_timestamp:
            try:
                starts_at = isoparse(starts_at_timestamp)
            except ValueError:
                _td = str_to_timedelta(starts_at_timestamp)
                starts_at = datetime.now(tzutc()) + _td

        if cluster_size > 1:
            log.debug(" -> cluster_mode:{} (replicate)", cluster_mode)

        if dependencies is None:
            dependencies = []

        session_creation_id = secrets.token_urlsafe(16)
        start_event = asyncio.Event()
        self.session_creation_tracker[session_creation_id] = start_event

        async with self.db.begin_readonly() as conn:
            # Use keypair bootstrap_script if it is not delivered as a parameter
            if not bootstrap_script:
                script, _ = await query_bootstrap_script(conn, owner_access_key)
                bootstrap_script = script

        public_sgroup_only = True
        if _role_str := image_row.labels.get("ai.backend.role"):
            public_sgroup_only = KernelRole(_role_str) not in PRIVATE_KERNEL_ROLES
        if dry_run:
            return {}
        try:
            session_id = await asyncio.shield(
                self.database_ptask_group.create_task(
                    self.enqueue_session(
                        session_creation_id,
                        session_name,
                        owner_access_key,
                        {
                            "creation_config": config,
                            "kernel_configs": [
                                {
                                    "image_ref": requested_image_ref,
                                    "cluster_role": DEFAULT_ROLE,
                                    "cluster_idx": 1,
                                    "local_rank": 0,
                                    "cluster_hostname": f"{DEFAULT_ROLE}1",
                                    "creation_config": config,
                                    "bootstrap_script": bootstrap_script,
                                    "startup_command": startup_command,
                                }
                            ],
                        },
                        config["scaling_group"],
                        session_type,
                        resource_policy,
                        user_scope=user_scope,
                        cluster_mode=cluster_mode,
                        cluster_size=cluster_size,
                        session_tag=tag,
                        starts_at=starts_at,
                        agent_list=config["agent_list"],
                        dependency_sessions=[SessionId(d) for d in dependencies],
                        callback_url=callback_url,
                        public_sgroup_only=public_sgroup_only,
                        route_id=route_id,
                        sudo_session_enabled=sudo_session_enabled,
                    )
                ),
            )
            resp["sessionId"] = str(session_id)  # changed since API v5
            resp["sessionName"] = str(session_name)
            resp["status"] = "PENDING"
            resp["servicePorts"] = []
            resp["created"] = True

            if not enqueue_only:
                self.pending_waits.add(current_task)
                max_wait = max_wait_seconds
                try:
                    if max_wait > 0:
                        with _timeout(max_wait):
                            await start_event.wait()
                    else:
                        await start_event.wait()
                except asyncio.TimeoutError:
                    resp["status"] = "TIMEOUT"
                else:
                    await asyncio.sleep(0.5)
                    async with self.db.begin_readonly_session() as db_sess:
                        query = sa.select(KernelRow.status, KernelRow.service_ports).where(
                            (KernelRow.session_id == session_id)
                            & (KernelRow.cluster_role == DEFAULT_ROLE)
                        )
                        result = await db_sess.execute(query)
                        row = result.first()
                    if row.status == KernelStatus.RUNNING:
                        resp["status"] = "RUNNING"
                        for item in row.service_ports:
                            response_dict = {
                                "name": item["name"],
                                "protocol": item["protocol"],
                                "ports": item["container_ports"],
                            }
                            if "url_template" in item.keys():
                                response_dict["url_template"] = item["url_template"]
                            if "allowed_arguments" in item.keys():
                                response_dict["allowed_arguments"] = item["allowed_arguments"]
                            if "allowed_envs" in item.keys():
                                response_dict["allowed_envs"] = item["allowed_envs"]
                            resp["servicePorts"].append(response_dict)
                    else:
                        resp["status"] = row.status.name
            return resp
        except asyncio.CancelledError:
            raise
        finally:
            self.pending_waits.discard(current_task)
            if not enqueue_only and session_creation_id in self.session_creation_tracker:
                del self.session_creation_tracker[session_creation_id]

    async def create_cluster(
        self,
        template: Any,
        session_name: str,
        user_scope: UserScope,
        owner_access_key: AccessKey,
        resource_policy: dict,
        scaling_group: str,
        sess_type: SessionTypes,
        tag: str,
        enqueue_only=False,
        max_wait_seconds=0,
        sudo_session_enabled=False,
    ) -> Mapping[str, Any]:
        resp: MutableMapping[str, Any] = {}

        current_task = asyncio.current_task()
        assert current_task is not None

        # Check existing (access_key, session) kernel instance
        try:
            # NOTE: We can reuse the session IDs of TERMINATED sessions only.
            # NOTE: Reusing a session in the PENDING status returns an empty value in service_ports.
            async with self.db.begin_readonly_session() as db_sess:
                await SessionRow.get_session(
                    db_sess,
                    session_name,
                    owner_access_key,
                )
        except SessionNotFound:
            pass
        else:
            raise TooManySessionsMatched

        mounts = []
        mount_map = {}
        environ = {}

        if _mounts := template["spec"].get("mounts"):  # noqa
            mounts = list(_mounts.keys())
            mount_map = {key: value for (key, value) in _mounts.items() if len(value) > 0}
        if _environ := template["spec"].get("environ"):  # noqa
            environ = _environ

        kernel_configs: List[KernelEnqueueingConfig] = []
        for node in template["spec"]["nodes"]:
            # Resolve session template.
            kernel_config = {
                "image": template["spec"]["kernel"]["image"],
                "architecture": template["spec"]["kernel"].get("architecture", DEFAULT_IMAGE_ARCH),
                "cluster_role": node["cluster_role"],
                "creation_config": {
                    "mount": mounts,
                    "mount_map": mount_map,
                    "environ": environ,
                },
            }

            if template["spec"]["sess_type"] == "interactive":
                kernel_config["sess_type"] = SessionTypes.INTERACTIVE
            elif template["spec"]["sess_type"] == "batch":
                kernel_config["sess_type"] = SessionTypes.BATCH
            elif template["spec"]["sess_type"] == "inference":
                kernel_config["sess_type"] = SessionTypes.INFERENCE

            if tag := template["metadata"].get("tag", None):
                kernel_config["tag"] = tag
            if runtime_opt := template["spec"]["kernel"]["run"]:
                if bootstrap := runtime_opt["bootstrap"]:
                    kernel_config["bootstrap_script"] = bootstrap
                if startup := runtime_opt["startup_command"]:
                    kernel_config["startup_command"] = startup

            if resources := template["spec"].get("resources"):
                kernel_config["creation_config"]["resources"] = resources

            if git := template["spec"]["kernel"]["git"]:
                if _dest := git.get("dest_dir"):
                    target = _dest
                else:
                    target = git["repository"].split("/")[-1]

                cmd_builder = "git clone "
                if credential := git.get("credential"):
                    proto, url = git["repository"].split("://")
                    cmd_builder += (
                        f'{proto}://{credential["username"]}:{credential["password"]}@{url}'
                    )
                else:
                    cmd_builder += git["repository"]
                if branch := git.get("branch"):
                    cmd_builder += f" -b {branch}"
                cmd_builder += f" {target}\n"

                if commit := git.get("commit"):
                    cmd_builder = "CWD=$(pwd)\n" + cmd_builder
                    cmd_builder += f"cd {target}\n"
                    cmd_builder += f"git checkout {commit}\n"
                    cmd_builder += "cd $CWD\n"

                bootstrap = base64.b64decode(kernel_config.get("bootstrap_script") or b"").decode()
                bootstrap += "\n"
                bootstrap += cmd_builder
                kernel_config["bootstrap_script"] = base64.b64encode(bootstrap.encode()).decode()

            # Resolve the image reference.
            try:
                async with self.db.begin_readonly_session() as session:
                    image_row = await ImageRow.resolve(
                        session,
                        [
                            ImageRef(kernel_config["image"], ["*"], kernel_config["architecture"]),
                            kernel_config["image"],
                        ],
                    )
                requested_image_ref = image_row.image_ref
                async with self.db.begin_readonly() as conn:
                    query = (
                        sa.select([domains.c.allowed_docker_registries])
                        .select_from(domains)
                        .where(domains.c.name == user_scope.domain_name)
                    )
                    allowed_registries = await conn.scalar(query)
                    if requested_image_ref.registry not in allowed_registries:
                        raise AliasResolutionFailed
                    kernel_config["image_ref"] = requested_image_ref
            except AliasResolutionFailed:
                raise ImageNotFound("unknown alias or disallowed registry")

            for i in range(node["replicas"]):
                kernel_config["cluster_idx"] = i + 1
                kernel_configs.append(
                    check_typed_dict(kernel_config, KernelEnqueueingConfig),  # type: ignore
                )

        session_creation_id = secrets.token_urlsafe(16)
        start_event = asyncio.Event()
        kernel_id: Optional[KernelId] = None
        self.session_creation_tracker[session_creation_id] = start_event
        current_task = asyncio.current_task()
        assert current_task is not None

        try:
            session_id = await asyncio.shield(
                self.database_ptask_group.create_task(
                    self.enqueue_session(
                        session_creation_id,
                        session_name,
                        owner_access_key,
                        {
                            "creation_config": {
                                "mount_map": mount_map,
                                "environ": environ,
                            },
                            "kernel_configs": kernel_configs,
                        },
                        scaling_group,
                        sess_type,
                        resource_policy,
                        user_scope=user_scope,
                        session_tag=tag,
                        sudo_session_enabled=sudo_session_enabled,
                    ),
                )
            )
            kernel_id = cast(KernelId, session_id)  # the main kernel's ID is the session ID.
            resp["kernelId"] = str(kernel_id)
            resp["status"] = "PENDING"
            resp["servicePorts"] = []
            resp["created"] = True

            if not enqueue_only:
                self.pending_waits.add(current_task)
                max_wait = max_wait_seconds
                try:
                    if max_wait > 0:
                        with _timeout(max_wait):
                            await start_event.wait()
                    else:
                        await start_event.wait()
                except asyncio.TimeoutError:
                    resp["status"] = "TIMEOUT"
                else:
                    await asyncio.sleep(0.5)
                    async with self.db.begin_readonly() as conn:
                        query = (
                            sa.select([
                                kernels.c.status,
                                kernels.c.service_ports,
                            ])
                            .select_from(kernels)
                            .where(kernels.c.id == kernel_id)
                        )
                        result = await conn.execute(query)
                        row = result.first()
                    if row["status"] == KernelStatus.RUNNING:
                        resp["status"] = "RUNNING"
                        for item in row["service_ports"]:
                            response_dict = {
                                "name": item["name"],
                                "protocol": item["protocol"],
                                "ports": item["container_ports"],
                            }
                            if "url_template" in item.keys():
                                response_dict["url_template"] = item["url_template"]
                            if "allowed_arguments" in item.keys():
                                response_dict["allowed_arguments"] = item["allowed_arguments"]
                            if "allowed_envs" in item.keys():
                                response_dict["allowed_envs"] = item["allowed_envs"]
                            resp["servicePorts"].append(response_dict)
                    else:
                        resp["status"] = row["status"].name
            return resp
        except asyncio.CancelledError:
            raise
        finally:
            self.pending_waits.discard(current_task)
            if session_creation_id in self.session_creation_tracker:
                del self.session_creation_tracker[session_creation_id]

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
        public_sgroup_only: bool = True,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        cluster_size: int = 1,
        session_tag: Optional[str] = None,
        internal_data: Optional[dict] = None,
        starts_at: Optional[datetime] = None,
        agent_list: Optional[Sequence[str]] = None,
        dependency_sessions: Optional[Sequence[SessionId]] = None,
        callback_url: Optional[URL] = None,
        route_id: Optional[uuid.UUID] = None,
        sudo_session_enabled: bool = False,
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
                "You cannot create session with more than "
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
                public_sgroup_only,
            )
            if scaling_group is None:
                log.warning(
                    f"enqueue_session(s:{session_name}, ak:{access_key}): "
                    "The client did not specify the scaling group for session; "
                    f"falling back to {checked_scaling_group}",
                )

            use_host_network_query = (
                sa.select([scaling_groups.c.use_host_network])
                .select_from(scaling_groups)
                .where(scaling_groups.c.name == checked_scaling_group)
            )
            use_host_network_result = await conn.execute(use_host_network_query)
            use_host_network = use_host_network_result.scalar()
            # Translate mounts/mount_map/mount_options into vfolder mounts
            requested_mounts = session_enqueue_configs["creation_config"].get("mounts") or []
            requested_mount_map = session_enqueue_configs["creation_config"].get("mount_map") or {}
            requested_mount_options = (
                session_enqueue_configs["creation_config"].get("mount_options") or {}
            )
            allowed_vfolder_types = await self.shared_config.get_vfolder_types()
            vfolder_mounts = await prepare_vfolder_mounts(
                conn,
                self.storage_manager,
                allowed_vfolder_types,
                user_scope,
                resource_policy,
                requested_mounts,
                requested_mount_map,
                requested_mount_options,
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
        if _fname := session_enqueue_configs["creation_config"].get("model_definition_path"):
            internal_data["model_definition_path"] = _fname
        if _variant := session_enqueue_configs["creation_config"].get("runtime_variant"):
            internal_data["runtime_variant"] = _variant

        if sudo_session_enabled:
            internal_data["sudo_session_enabled"] = True

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
            "use_host_network": use_host_network,
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
        session_images: list[str] = []

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
            service_ports = parse_service_ports(
                labels.get("ai.backend.service-ports", ""),
                labels.get("ai.backend.endpoint-ports", ""),
                BackendError,
            )
            preopen_ports: Sequence[int] = creation_config.get("preopen_ports") or []

            for preopen_port in preopen_ports:
                if preopen_port in (2000, 2001, 2200, 7681):
                    raise InvalidAPIParameters(
                        "Port 2000, 2001, 2200 and 7681 are reserved for internal use"
                    )
                for service_port in service_ports:
                    if preopen_port in service_port["container_ports"]:
                        raise InvalidAPIParameters(
                            "Preopen port allocation cannot overlap with service port predefined by image"
                        )

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
            if (resources := creation_config.get("resources")) is not None:
                # Sanitize user input: does it have "known" resource slots only?
                for slot_key, slot_value in resources.items():
                    if slot_key not in known_slot_types:
                        raise InvalidAPIParameters(f"Unknown requested resource slot: {slot_key}")
                try:
                    requested_slots = ResourceSlot.from_user_input(resources, known_slot_types)
                except ValueError:
                    log.exception("request_slots & image_slots calculation error")
                    # happens when requested_slots have more keys
                    # than the image-defined slots
                    # (e.g., image does not support accelerators
                    #  requested by the client)
                    raise InvalidAPIParameters(
                        "Your resource request has resource type(s) not supported by the image."
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
                    raise InvalidAPIParameters("Client upgrade required to use GPUs (v19.03+).")
                tpu = creation_config.get("instanceTPUs")
                if tpu is not None:
                    raise InvalidAPIParameters("Client upgrade required to use TPUs (v19.03+).")

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

            kernel_data.append({
                **kernel_shared_data,
                "id": kernel_id,
                "agent": mapped_agent,
                "cluster_role": kernel["cluster_role"],
                "cluster_idx": kernel["cluster_idx"],
                "local_rank": kernel["local_rank"],
                "cluster_hostname": (
                    f"{kernel['cluster_role']}{kernel['cluster_idx']}"
                    if not kernel["cluster_hostname"]
                    else kernel["cluster_hostname"]
                ),
                "image": image_ref.canonical,
                # "image_id": image_row.id,
                "architecture": image_ref.architecture,
                "registry": image_ref.registry,
                "role": KernelRole(image_row.labels.get("ai.backend.role", KernelRole.COMPUTE)),
                "startup_command": kernel.get("startup_command"),
                "occupied_slots": requested_slots,
                "requested_slots": requested_slots,
                "resource_opts": resource_opts,
                "environ": [f"{k}={v}" for k, v in environ.items()],
                "bootstrap_script": kernel.get("bootstrap_script"),
                "preopen_ports": preopen_ports,
            })

            if image_ref.canonical not in session_images:
                if kernel["cluster_role"] == DEFAULT_ROLE:
                    session_images.insert(0, image_ref.canonical)
                else:
                    session_images.append(image_ref.canonical)
        session_data["images"] = session_images
        try:

            async def _enqueue() -> None:
                async with self.db.begin_session() as db_sess:
                    matched_dependency_session_ids = []
                    if dependency_sessions:
                        for dependency_id in dependency_sessions:
                            try:
                                match_info = await SessionRow.get_session(
                                    db_sess,
                                    dependency_id,
                                    access_key,
                                    allow_stale=True,
                                )
                            except SessionNotFound:
                                raise InvalidAPIParameters(
                                    "Unknown session ID or name in the dependency list",
                                    extra_data={"session_ref": dependency_id},
                                )
                            else:
                                matched_dependency_session_ids.append(match_info.id)

                    if sudo_session_enabled:
                        environ["SUDO_SESSION_ENABLED"] = "1"

                    session_data["environ"] = environ
                    session_data["requested_slots"] = session_requested_slots
                    session = SessionRow(**session_data)
                    kernels = [KernelRow(**kernel) for kernel in kernel_data]
                    db_sess.add(session)
                    db_sess.add_all(kernels)
                    await db_sess.flush()

                    if matched_dependency_session_ids:
                        dependency_rows = [
                            SessionDependencyRow(session_id=session_id, depends_on=depend_id)
                            for depend_id in matched_dependency_session_ids
                        ]
                        db_sess.add_all(dependency_rows)

            await execute_with_retry(_enqueue)

            async def _post_enqueue() -> None:
                async with self.db.begin_session() as db_sess:
                    if route_id:
                        routing_row = await RoutingRow.get(db_sess, route_id)
                        routing_row.session = session_id

                    await db_sess.commit()

            await execute_with_retry(_post_enqueue)
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
        auto_pull = self.shared_config["docker"]["image"]["auto_pull"]

        # Aggregate image registry information
        keyfunc = lambda item: item.kernel.image_ref
        image_infos: MutableMapping[str, ImageRow] = {}
        is_local_image = True
        registry_url = URL("http://localhost")
        registry_creds: dict[str, str] = {}
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
                resolved_image_info = await ImageRow.resolve(session, [image_ref])
                image_infos[str(image_ref)] = resolved_image_info
                if not resolved_image_info.image_ref.is_local:
                    is_local_image = False
                    registry_url, registry_creds = await get_registry_info(
                        self.shared_config.etcd, image_ref.registry
                    )
        image_info = {
            "image_infos": image_infos,
            "registry_url": registry_url,
            "registry_creds": registry_creds,
            "resource_policy": resource_policy,
            "auto_pull": auto_pull,
            "is_local": is_local_image,
        }

        network_name: Optional[str] = None
        cluster_ssh_port_mapping: Optional[Dict[str, Tuple[str, int]]] = None
        if not scheduled_session.use_host_network:
            if scheduled_session.cluster_mode == ClusterMode.SINGLE_NODE:
                if scheduled_session.cluster_size > 1:
                    network_name = f"bai-singlenode-{scheduled_session.id}"
                    agent_alloc_ctx = kernel_agent_bindings[0].agent_alloc_ctx
                    assert agent_alloc_ctx.agent_id is not None
                    assert scheduled_session.id is not None
                    try:
                        async with self.agent_cache.rpc_context(
                            agent_alloc_ctx.agent_id,
                            order_key=str(scheduled_session.main_kernel.id),
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
                mtu = self.shared_config["network"]["overlay"]["mtu"]
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
                        create_options["Options"] = {"com.docker.network.driver.mtu": str(mtu)}
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
                        async with self.agent_cache.rpc_context(
                            item.agent_alloc_ctx.agent_id,
                            order_key=str(scheduled_session.id),
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
            ssh_keypair=await self.create_cluster_ssh_keypair(),
            cluster_ssh_port_mapping=cast(
                Optional[ClusterSSHPortMapping], cluster_ssh_port_mapping
            ),
        )

        async with self.db.begin_readonly_session() as db_sess:
            uuid, email, username = (
                await db_sess.execute(
                    sa.select([UserRow.uuid, UserRow.email, UserRow.username]).where(
                        UserRow.uuid == scheduled_session.user_uuid
                    )
                )
            ).fetchone()

        scheduled_session.environ.update({
            "BACKENDAI_USER_UUID": str(uuid),
            "BACKENDAI_USER_EMAIL": email,
            "BACKENDAI_USER_NAME": username,
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
            "BACKENDAI_PREOPEN_PORTS": (
                ",".join(str(port) for port in scheduled_session.main_kernel.preopen_ports)
                if scheduled_session.main_kernel.preopen_ports is not None
                else ""
            ),
        })

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
                    agent_errors,
                )
            await self.settle_agent_alloc(kernel_agent_bindings)

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

    async def finalize_running(
        self, kernel_id: KernelId, session_id: SessionId, created_info: Mapping[str, Any]
    ) -> None:
        try:
            agent_host = URL(created_info["agent_addr"]).host
            kernel_host = created_info.get("kernel_host", agent_host)
            service_ports = created_info.get("service_ports", [])
            actual_allocs = self.convert_resource_spec_to_resource_slot(
                created_info["resource_spec"]["allocations"]
            )
            new_status = KernelStatus.RUNNING
            update_data = {
                "occupied_slots": actual_allocs,
                "scaling_group": created_info["scaling_group"],
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
                        new_status.name: datetime.now(tzutc()).isoformat(),
                    },
                ),
            }
            self._kernel_actual_allocated_resources[kernel_id] = actual_allocs

            async def _update_session_occupying_slots() -> None:
                async with self.db.begin_session() as db_session:
                    _stmt = sa.select(SessionRow).where(SessionRow.id == session_id)
                    session_row = cast(SessionRow | None, await db_session.scalar(_stmt))
                    if session_row is None:
                        raise SessionNotFound(f"Failed to fetch session (id:{session_id})")
                    session_occupying_slots = ResourceSlot.from_json({
                        **session_row.occupying_slots
                    })
                    session_occupying_slots.sync_keys(actual_allocs)
                    for key, val in session_occupying_slots.items():
                        session_occupying_slots[key] = str(
                            Decimal(val) + Decimal(actual_allocs[key])
                        )
                    session_row.occupying_slots = session_occupying_slots

            await execute_with_retry(_update_session_occupying_slots)
            kernel_did_update = await KernelRow.update_kernel(
                self.db, kernel_id, new_status, update_data=update_data
            )
            if not kernel_did_update:
                return
            new_session_status = await SessionRow.transit_session_status(self.db, session_id)
            if new_session_status is None or new_session_status != SessionStatus.RUNNING:
                return
            query = (
                sa.select(SessionRow)
                .where(SessionRow.id == session_id)
                .options(
                    noload("*"),
                    load_only(
                        SessionRow.id,
                        SessionRow.name,
                        SessionRow.creation_id,
                        SessionRow.access_key,
                        SessionRow.session_type,
                    ),
                    selectinload(
                        SessionRow.kernels,
                    ).options(
                        load_only(
                            KernelRow.id,
                            KernelRow.agent,
                            KernelRow.cluster_role,
                            KernelRow.startup_command,
                        )
                    ),
                    with_loader_criteria(KernelRow, KernelRow.cluster_role == DEFAULT_ROLE),
                )
            )
            async with self.db.begin_readonly_session() as db_session:
                updated_session = cast(SessionRow, await db_session.scalar(query))

            log.debug(
                "Producing SessionStartedEvent({}, {})",
                updated_session.id,
                updated_session.creation_id,
            )
            await self.event_producer.produce_event(
                SessionStartedEvent(updated_session.id, updated_session.creation_id),
            )
            await self.hook_plugin_ctx.notify(
                "POST_START_SESSION",
                (
                    updated_session.id,
                    updated_session.name,
                    updated_session.access_key,
                ),
            )

            if updated_session.session_type == SessionTypes.BATCH:
                await self.trigger_batch_execution(updated_session)
        except Exception:
            log.exception("error while executing _finalize_running")
            raise

    async def _create_kernels_in_one_agent(
        self,
        agent_alloc_ctx: AgentAllocationContext,
        scheduled_session: SessionRow,
        items: Sequence[KernelAgentBinding],
        image_info: Mapping[str, Any],
        cluster_info,
    ) -> None:
        registry_url = image_info["registry_url"]
        registry_creds = image_info["registry_creds"]
        image_infos = image_info["image_infos"]
        is_local = image_info["is_local"]
        resource_policy: KeyPairResourcePolicyRow = image_info["resource_policy"]
        auto_pull = image_info["auto_pull"]
        assert agent_alloc_ctx.agent_id is not None
        assert scheduled_session.id is not None

        async def _update_kernel() -> None:
            async with self.db.begin_session() as db_sess:
                kernel_query = (
                    sa.update(KernelRow)
                    .where(KernelRow.id.in_([binding.kernel.id for binding in items]))
                    .values(
                        agent=agent_alloc_ctx.agent_id,
                        agent_addr=agent_alloc_ctx.agent_addr,
                        scaling_group=agent_alloc_ctx.scaling_group,
                    )
                )
                await db_sess.execute(kernel_query)

        await execute_with_retry(_update_kernel)

        async with self.agent_cache.rpc_context(
            agent_alloc_ctx.agent_id,
            order_key=str(scheduled_session.id),
        ) as rpc:
            try:
                get_image_ref = lambda k: image_infos[str(k.image_ref)].image_ref
                # Issue a batched RPC call to create kernels on this agent
                # created_infos = await rpc.call.create_kernels(
                await rpc.call.create_kernels(
                    str(scheduled_session.id),
                    [str(binding.kernel.id) for binding in items],
                    [
                        {
                            "image": {
                                # TODO: refactor registry and is_local to be specified per kernel.
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
                                "is_local": is_local,
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
            except (asyncio.TimeoutError, asyncio.CancelledError):
                log.warning("_create_kernels_in_one_agent(s:{}) cancelled", scheduled_session.id)
            except Exception as e:
                # The agent has already cancelled or issued the destruction lifecycle event
                # for this batch of kernels.
                ex = e
                for binding in items:
                    kernel_id = binding.kernel.id

                    async def _update_failure() -> None:
                        async with self.db.begin_session() as db_sess:
                            now = datetime.now(tzutc())
                            query = (
                                sa.update(KernelRow)
                                .where(KernelRow.id == kernel_id)
                                .values(
                                    status=KernelStatus.ERROR,
                                    status_info=f"other-error ({ex!r})",
                                    status_changed=now,
                                    terminated_at=now,
                                    status_history=sql_json_merge(
                                        KernelRow.status_history,
                                        (),
                                        {
                                            KernelStatus.ERROR.name: (
                                                now.isoformat()
                                            ),  # ["PULLING", "PREPARING"]
                                        },
                                    ),
                                    status_data=convert_to_status_data(ex, self.debug),
                                )
                            )
                            await db_sess.execute(query)

                    await execute_with_retry(_update_failure)
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

    async def get_user_occupancy(self, user_id, *, db_sess=None):
        known_slot_types = await self.shared_config.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                query = sa.select(KernelRow.occupied_slots).where(
                    (KernelRow.user_uuid == user_id)
                    & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                    & (KernelRow.role.not_in(PRIVATE_KERNEL_ROLES)),
                )
                zero = ResourceSlot()
                user_occupied = sum(
                    [row.occupied_slots async for row in (await _sess.stream(query))], zero
                )
                # drop no-longer used slot types
                user_occupied = ResourceSlot({
                    key: val for key, val in user_occupied.items() if key in known_slot_types
                })
                return user_occupied

        return await execute_with_retry(_query)

    async def get_keypair_occupancy(self, access_key, *, db_sess=None):
        known_slot_types = await self.shared_config.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                query = sa.select(KernelRow.occupied_slots).where(
                    (KernelRow.access_key == access_key)
                    & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                    & (KernelRow.role.not_in(PRIVATE_KERNEL_ROLES)),
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
                    & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                    & (KernelRow.role.not_in(PRIVATE_KERNEL_ROLES)),
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
                    & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                    & (KernelRow.role.not_in(PRIVATE_KERNEL_ROLES)),
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
        async with self.agent_cache.rpc_context(agent["id"]) as rpc:
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

                async def _update_agent_resource() -> None:
                    async with self.db.begin_session() as db_sess:
                        select_query = sa.select(AgentRow.occupied_slots).where(
                            AgentRow.id == agent_id
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

                await execute_with_retry(_update_agent_resource)

    async def recalc_resource_usage(self, do_fullscan: bool = False) -> None:
        async def _recalc() -> Mapping[AccessKey, ConcurrencyUsed]:
            occupied_slots_per_agent: MutableMapping[str, ResourceSlot] = defaultdict(
                lambda: ResourceSlot({"cpu": 0, "mem": 0})
            )
            access_key_to_concurrency_used: dict[AccessKey, ConcurrencyUsed] = {}

            async with self.db.begin_session() as db_sess:
                # Query running containers and calculate concurrency_used per AK and
                # occupied_slots per agent.
                session_query = (
                    sa.select(SessionRow)
                    .where(
                        (
                            SessionRow.status.in_({
                                *AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
                                *USER_RESOURCE_OCCUPYING_SESSION_STATUSES,
                            })
                        )
                    )
                    .options(
                        load_only(SessionRow.id, SessionRow.access_key, SessionRow.status),
                        selectinload(SessionRow.kernels).options(
                            load_only(KernelRow.agent, KernelRow.role, KernelRow.occupied_slots)
                        ),
                    )
                )
                async for session_row in await db_sess.stream_scalars(session_query):
                    session_row = cast(SessionRow, session_row)
                    for kernel in session_row.kernels:
                        session_status = cast(SessionStatus, session_row.status)
                        if session_status in AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES:
                            occupied_slots_per_agent[kernel.agent] += ResourceSlot(
                                kernel.occupied_slots
                            )
                        if session_status in USER_RESOURCE_OCCUPYING_SESSION_STATUSES:
                            access_key = cast(AccessKey, session_row.access_key)
                            if access_key not in access_key_to_concurrency_used:
                                access_key_to_concurrency_used[access_key] = ConcurrencyUsed(
                                    access_key
                                )
                            if kernel.role in PRIVATE_KERNEL_ROLES:
                                access_key_to_concurrency_used[access_key].system_session_ids.add(
                                    session_row.id
                                )
                            else:
                                access_key_to_concurrency_used[access_key].compute_session_ids.add(
                                    session_row.id
                                )

                if len(occupied_slots_per_agent) > 0:
                    # Update occupied_slots for agents with running containers.
                    await db_sess.execute(
                        (
                            sa.update(AgentRow)
                            .where(AgentRow.id == sa.bindparam("agent_id"))
                            .values(occupied_slots=sa.bindparam("occupied_slots"))
                        ),
                        [
                            {"agent_id": aid, "occupied_slots": slots}
                            for aid, slots in occupied_slots_per_agent.items()
                        ],
                    )
                    await db_sess.execute(
                        (
                            sa.update(AgentRow)
                            .values(occupied_slots=ResourceSlot({}))
                            .where(AgentRow.status == AgentStatus.ALIVE)
                            .where(sa.not_(AgentRow.id.in_(occupied_slots_per_agent.keys())))
                        )
                    )
                else:
                    query = (
                        sa.update(AgentRow)
                        .values(occupied_slots=ResourceSlot({}))
                        .where(AgentRow.status == AgentStatus.ALIVE)
                    )
                    await db_sess.execute(query)
            return access_key_to_concurrency_used

        access_key_to_concurrency_used = await execute_with_retry(_recalc)

        # Update keypair resource usage for keypairs with running containers.
        async def _update(r: Redis):
            updates: dict[str, int] = {}
            for concurrency in access_key_to_concurrency_used.values():
                updates |= concurrency.to_cnt_map()
            if updates:
                await r.mset(typing.cast(MSetType, updates))

        async def _update_by_fullscan(r: Redis):
            updates = {}
            keys = await r.keys(f"{COMPUTE_CONCURRENCY_USED_KEY_PREFIX}*")
            for stat_key in keys:
                if isinstance(stat_key, bytes):
                    _stat_key = stat_key.decode("utf-8")
                else:
                    _stat_key = cast(str, stat_key)
                ak = _stat_key.replace(COMPUTE_CONCURRENCY_USED_KEY_PREFIX, "")
                concurrent_sessions = access_key_to_concurrency_used.get(AccessKey(ak))
                usage = (
                    len(concurrent_sessions.compute_session_ids)
                    if concurrent_sessions is not None
                    else 0
                )
                updates[_stat_key] = usage
            keys = await r.keys(f"{SYSTEM_CONCURRENCY_USED_KEY_PREFIX}*")
            for stat_key in keys:
                if isinstance(stat_key, bytes):
                    _stat_key = stat_key.decode("utf-8")
                else:
                    _stat_key = cast(str, stat_key)
                ak = _stat_key.replace(SYSTEM_CONCURRENCY_USED_KEY_PREFIX, "")
                concurrent_sessions = access_key_to_concurrency_used.get(AccessKey(ak))
                usage = (
                    len(concurrent_sessions.system_concurrency_used_key)
                    if concurrent_sessions is not None
                    else 0
                )
                updates[_stat_key] = usage
            if updates:
                await r.mset(typing.cast(MSetType, updates))

        # Do full scan if the entire system does not have ANY sessions/sftp-sessions
        # to set all concurrency_used to 0
        _do_fullscan = do_fullscan or not access_key_to_concurrency_used
        if _do_fullscan:
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
            async with self.agent_cache.rpc_context(
                destroyed_kernels[0]["agent"], order_key=str(session_id)
            ) as rpc:
                for kernel in destroyed_kernels:
                    # internally it enqueues a "destroy" lifecycle event.
                    rpc_coros.append(
                        rpc.call.destroy_kernel(
                            str(kernel["id"]),
                            str(session_id),
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
        user_role: UserRole | None = None,
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

        async def _force_destroy_for_suadmin(
            target_status: Literal[SessionStatus.CANCELLED, SessionStatus.TERMINATED],
        ) -> None:
            current_time = datetime.now(tzutc())
            destroy_reason = str(KernelLifecycleEventReason.FORCE_TERMINATED)

            async def _destroy() -> SessionRow:
                async with self.db.begin_session() as db_session:
                    _stmt = (
                        sa.select(SessionRow)
                        .where(SessionRow.id == session_id)
                        .options(selectinload(SessionRow.kernels))
                    )
                    session_row = cast(SessionRow | None, await db_session.scalar(_stmt))
                    if session_row is None:
                        raise SessionNotFound(f"Session not found (id: {session_id})")
                    kernel_rows = cast(list[KernelRow], session_row.kernels)
                    kernel_target_status = SESSION_KERNEL_STATUS_MAPPING[target_status]
                    for kern in kernel_rows:
                        kern.status = kernel_target_status
                        kern.terminated_at = current_time
                        kern.status_info = destroy_reason
                        kern.status_history = sql_json_merge(
                            KernelRow.status_history,
                            (),
                            {
                                kernel_target_status.name: current_time.isoformat(),
                            },
                        )
                    session_row.status = target_status
                    session_row.terminated_at = current_time
                    session_row.status_info = destroy_reason
                    session_row.status_history = sql_json_merge(
                        SessionRow.status_history,
                        (),
                        {
                            target_status.name: current_time.isoformat(),
                        },
                    )
                    return session_row

            await execute_with_retry(_destroy)
            await self.recalc_resource_usage()

        async with handle_session_exception(
            self.db,
            "destroy_session",
            session_id,
            set_error=True,
        ):
            query = (
                sa.select(SessionRow)
                .where(SessionRow.id == session_id)
                .options(
                    noload("*"),
                    load_only(SessionRow.creation_id, SessionRow.status),
                    selectinload(SessionRow.kernels).options(
                        noload("*"),
                        load_only(
                            KernelRow.id,
                            KernelRow.role,
                            KernelRow.access_key,
                            KernelRow.status,
                            KernelRow.container_id,
                            KernelRow.cluster_role,
                            KernelRow.agent,
                            KernelRow.agent_addr,
                        ),
                    ),
                )
            )
            async with self.db.begin_readonly_session() as db_session:
                target_session = (await db_session.scalars(query)).first()
            if not target_session:
                raise SessionNotFound

            match target_session.status:
                case SessionStatus.PENDING:
                    await SessionRow.set_session_status(
                        self.db, session_id, SessionStatus.CANCELLED
                    )
                case SessionStatus.PULLING:
                    # Exceptionally allow superadmins to destroy PULLING sessions.
                    # Clients should be informed that they have to handle the containers destroyed here.
                    # TODO: detach image-pull process from kernel-start process and allow all users to destroy PULLING sessions.
                    if forced and user_role == UserRole.SUPERADMIN:
                        log.warning(
                            "force-terminating session (s:{}, status:{})",
                            session_id,
                            target_session.status,
                        )
                        await _force_destroy_for_suadmin(SessionStatus.CANCELLED)
                        return {}
                    raise GenericForbidden("Cannot destroy sessions in pulling status")
                case (
                    SessionStatus.SCHEDULED
                    | SessionStatus.PREPARING
                    | SessionStatus.TERMINATING
                    | SessionStatus.ERROR
                ):
                    if not forced:
                        raise GenericForbidden(
                            "Cannot destroy sessions in scheduled/preparing/terminating/error"
                            " status",
                        )
                    log.warning(
                        "force-terminating session (s:{}, status:{})",
                        session_id,
                        target_session.status,
                    )
                    if user_role == UserRole.SUPERADMIN:
                        # Exceptionally let superadmins set the session status to 'TERMINATED' and finish the function.
                        # TODO: refactor Session/Kernel status management and remove this.
                        await _force_destroy_for_suadmin(SessionStatus.TERMINATED)
                        return {}
                    else:
                        await SessionRow.set_session_status(
                            self.db, session_id, SessionStatus.TERMINATING
                        )
                        await self.event_producer.produce_event(
                            SessionTerminatingEvent(session_id, reason),
                        )
                case SessionStatus.TERMINATED:
                    raise GenericForbidden(
                        "Cannot destroy sessions that has already been already terminated"
                    )
                case SessionStatus.CANCELLED:
                    raise GenericForbidden(
                        "Cannot destroy sessions that has already been already cancelled"
                    )
                case _:
                    await SessionRow.set_session_status(
                        self.db, session_id, SessionStatus.TERMINATING
                    )
                    await self.event_producer.produce_event(
                        SessionTerminatingEvent(session_id, reason),
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
                            await KernelRow.set_kernel_status(
                                self.db,
                                kernel.id,
                                KernelStatus.CANCELLED,
                                reason=reason,
                                status_changed_at=now,
                            )
                            await self.event_producer.produce_event(
                                KernelCancelledEvent(kernel.id, session_id, reason),
                            )
                            if kernel.cluster_role == DEFAULT_ROLE:
                                main_stat = {"status": "cancelled"}
                                await SessionRow.set_session_status(
                                    self.db,
                                    session_id,
                                    SessionStatus.CANCELLED,
                                    reason=reason,
                                    status_changed_at=now,
                                )
                                await self.event_producer.produce_event(
                                    SessionCancelledEvent(
                                        session_id,
                                        target_session.creation_id,
                                        reason,
                                    ),
                                )
                        case KernelStatus.PULLING:
                            raise GenericForbidden("Cannot destroy kernels in pulling status")
                        case (
                            KernelStatus.SCHEDULED
                            | KernelStatus.PREPARING
                            | KernelStatus.TERMINATING
                            | KernelStatus.ERROR
                        ):
                            if not forced:
                                raise GenericForbidden(
                                    "Cannot destroy kernels in"
                                    " scheduled/preparing/terminating/error status",
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
                                if kernel.is_private:
                                    kp_key = "keypair.sftp_concurrency_used"
                                else:
                                    kp_key = "keypair.concurrency_used"
                                await redis_helper.execute(
                                    self.redis_stat,
                                    lambda r: r.incrby(
                                        f"{kp_key}.{kernel.access_key}",
                                        -1,
                                    ),
                                )

                            await execute_with_retry(_update)
                            await self.event_producer.produce_event(
                                KernelTerminatedEvent(kernel.id, target_session.id, reason),
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
                                if kernel.is_private:
                                    kp_key = "keypair.sftp_concurrency_used"
                                else:
                                    kp_key = "keypair.concurrency_used"
                                await redis_helper.execute(
                                    self.redis_stat,
                                    lambda r: r.incrby(
                                        f"{kp_key}.{kernel.access_key}",
                                        -1,
                                    ),
                                )

                            await execute_with_retry(_update)
                            await self.event_producer.produce_event(
                                KernelTerminatingEvent(kernel.id, target_session.id, reason),
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
                    async with self.agent_cache.rpc_context(
                        destroyed_kernels[0].agent, order_key=session.id
                    ) as rpc:
                        rpc_coros = []
                        for kernel in destroyed_kernels:
                            # internally it enqueues a "destroy" lifecycle event.
                            if kernel.status != KernelStatus.SCHEDULED:
                                rpc_coros.append(
                                    rpc.call.destroy_kernel(
                                        str(kernel.id), str(session.id), reason
                                    ),
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
                    KernelTerminatedEvent(kernel.id, target_session.id, reason),
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
        async def _fetch_session() -> Row:
            async with self.db.begin_readonly() as conn:
                query = (
                    sa.select([
                        kernels.c.session_id,
                        kernels.c.cluster_mode,
                        kernels.c.cluster_size,
                        kernels.c.agent,
                        kernels.c.agent_addr,
                        kernels.c.use_host_network,
                    ])
                    .select_from(kernels)
                    .where(
                        (kernels.c.session_id == session_id)
                        & (kernels.c.cluster_role == DEFAULT_ROLE)
                    )
                )
                result = await conn.execute(query)
                return result.first()

        session = await execute_with_retry(_fetch_session)
        if session is None:
            return
        # Get the main container's agent info
        if not session["use_host_network"]:
            if session["cluster_mode"] == ClusterMode.SINGLE_NODE and session["cluster_size"] > 1:
                network_name = f'bai-singlenode-{session["session_id"]}'
                try:
                    async with self.agent_cache.rpc_context(
                        session["agent"],
                        order_key=session["session_id"],
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
            try:
                async with self.agent_cache.rpc_context(
                    kernel.agent,  # the main-container's agent
                    order_key=None,
                ) as rpc:
                    updated_config: Dict[str, Any] = {
                        # TODO: support rescaling of sub-containers
                    }
                    kernel_info = await rpc.call.restart_kernel(
                        str(kernel.session_id),
                        str(kernel.id),
                        updated_config,
                    )

                now = datetime.now(tzutc())
                update_data = {
                    "container_id": kernel_info["container_id"],
                    "repl_in_port": kernel_info["repl_in_port"],
                    "repl_out_port": kernel_info["repl_out_port"],
                    "stdin_port": kernel_info["stdin_port"],
                    "stdout_port": kernel_info["stdout_port"],
                    "service_ports": kernel_info.get("service_ports", []),
                    "status_history": sql_json_merge(
                        KernelRow.status_history,
                        (),
                        {
                            KernelStatus.RUNNING.name: now.isoformat(),
                        },
                    ),
                }
                await KernelRow.update_kernel(
                    self.db, kernel.id, KernelStatus.RUNNING, update_data=update_data
                )
            except Exception:
                log.exception("unexpected-error in _restart_kernel()")

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

        await SessionRow.set_session_status(self.db, session.id, SessionStatus.RUNNING)

        # NOTE: If the restarted session is a batch-type one, then the startup command
        #       will be executed again after restart.
        await self.event_producer.produce_event(
            SessionStartedEvent(session.id, session.creation_id),
        )

        if session.session_type == SessionTypes.BATCH:
            await self.trigger_batch_execution(session)

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
            async with self.agent_cache.rpc_context(
                session.main_kernel.agent,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
            ) as rpc:
                return await rpc.call.execute(
                    str(session.id),
                    str(session.main_kernel.id),
                    major_api_version,
                    run_id,
                    mode,
                    code,
                    opts,
                    flush_timeout,
                )

    async def trigger_batch_execution(
        self,
        session: SessionRow,
    ) -> None:
        async with handle_session_exception(self.db, "trigger_batch_execution", session.id):
            async with self.agent_cache.rpc_context(
                session.main_kernel.agent,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
            ) as rpc:
                return await rpc.call.trigger_batch_execution(
                    str(session.id),
                    str(session.main_kernel.id),
                    session.main_kernel.startup_command or "",
                )

    async def interrupt_session(
        self,
        session: SessionRow,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            async with self.agent_cache.rpc_context(
                session.main_kernel.agent,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
            ) as rpc:
                return await rpc.call.interrupt_kernel(str(session.main_kernel.id))

    async def get_completions(
        self,
        session: SessionRow,
        text: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            async with self.agent_cache.rpc_context(
                session.main_kernel.agent,
                invoke_timeout=10,
                order_key=session.main_kernel.id,
            ) as rpc:
                return await rpc.call.get_completions(str(session.main_kernel.id), text, opts)

    async def start_service(
        self,
        session: SessionRow,
        service: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            async with self.agent_cache.rpc_context(
                session.main_kernel.agent,
                order_key=session.main_kernel.id,
            ) as rpc:
                return await rpc.call.start_service(str(session.main_kernel.id), service, opts)

    async def shutdown_service(
        self,
        session: SessionRow,
        service: str,
    ) -> None:
        async with handle_session_exception(self.db, "shutdown_service", session.id):
            async with self.agent_cache.rpc_context(
                session.main_kernel.agent,
                order_key=session.main_kernel.id,
            ) as rpc:
                return await rpc.call.shutdown_service(str(session.main_kernel.id), service)

    async def upload_file(
        self,
        session: SessionRow,
        filename: str,
        payload: bytes,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "upload_file", session.id):
            async with self.agent_cache.rpc_context(
                session.main_kernel.agent,
                order_key=session.main_kernel.id,
            ) as rpc:
                return await rpc.call.upload_file(str(session.main_kernel.id), filename, payload)

    async def download_file(
        self,
        session: SessionRow,
        filepath: str,
    ) -> bytes:
        kernel = session.main_kernel
        async with handle_session_exception(self.db, "download_file", kernel.session_id):
            async with self.agent_cache.rpc_context(kernel.agent, order_key=kernel.id) as rpc:
                return await rpc.call.download_file(str(kernel.id), filepath)

    async def download_single(
        self,
        session: SessionRow,
        access_key: AccessKey,
        filepath: str,
    ) -> bytes:
        kernel = session.main_kernel
        async with handle_session_exception(self.db, "download_single", kernel.session_id):
            async with self.agent_cache.rpc_context(kernel.agent, order_key=kernel.id) as rpc:
                return await rpc.call.download_single(str(kernel.id), filepath)

    async def list_files(
        self,
        session: SessionRow,
        path: str,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "list_files", session.id):
            async with self.agent_cache.rpc_context(
                session.main_kernel.agent,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
            ) as rpc:
                return await rpc.call.list_files(str(session.main_kernel.id), path)

    async def get_logs_from_agent(
        self,
        session: SessionRow,
        kernel_id: KernelId | None = None,
    ) -> str:
        async with handle_session_exception(self.db, "get_logs_from_agent", session.id):
            kernel = (
                session.get_kernel_by_id(kernel_id)
                if kernel_id is not None
                else session.main_kernel
            )
            async with self.agent_cache.rpc_context(
                agent_id=kernel.agent,
                invoke_timeout=30,
                order_key=kernel.id,
            ) as rpc:
                reply = await rpc.call.get_logs(str(kernel.id))
                return reply["logs"]

    async def increment_session_usage(
        self,
        session: SessionRow,
    ) -> None:
        # noop for performance reasons
        pass

    async def kill_all_sessions_in_agent(self, agent_id, agent_addr):
        async with self.agent_cache.rpc_context(agent_id) as rpc:
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
        available_slots = ResourceSlot({
            SlotName(k): Decimal(v[1]) for k, v in agent_info["resource_slots"].items()
        })
        current_addr = agent_info["addr"]
        sgroup = agent_info.get("scaling_group", "default")
        auto_terminate_abusing_kernel = agent_info.get("auto_terminate_abusing_kernel", False)
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
                        sa.select([
                            agents.c.status,
                            agents.c.addr,
                            agents.c.public_host,
                            agents.c.public_key,
                            agents.c.scaling_group,
                            agents.c.available_slots,
                            agents.c.version,
                            agents.c.compute_plugins,
                            agents.c.architecture,
                            agents.c.auto_terminate_abusing_kernel,
                        ])
                        .select_from(agents)
                        .where(agents.c.id == agent_id)
                        .with_for_update()
                    )
                    result = await conn.execute(fetch_query)
                    row = result.first()

                    if row is None or row["status"] is None:
                        # new agent detected!
                        log.info("instance_lifecycle: agent {0} joined (via heartbeat)!", agent_id)
                        await self.shared_config.update_resource_slots(slot_key_and_units)
                        self.agent_cache.update(
                            agent_id,
                            current_addr,
                            agent_info["public_key"],
                        )
                        insert_query = sa.insert(agents).values({
                            "id": agent_id,
                            "status": AgentStatus.ALIVE,
                            "region": agent_info["region"],
                            "scaling_group": sgroup,
                            "available_slots": available_slots,
                            "occupied_slots": {},
                            "addr": agent_info["addr"],
                            "public_host": agent_info["public_host"],
                            "public_key": agent_info["public_key"],
                            "first_contact": now,
                            "lost_at": sa.null(),
                            "version": agent_info["version"],
                            "compute_plugins": agent_info["compute_plugins"],
                            "architecture": agent_info.get("architecture", "x86_64"),
                            "auto_terminate_abusing_kernel": auto_terminate_abusing_kernel,
                        })
                        result = await conn.execute(insert_query)
                        assert result.rowcount == 1
                    elif row["status"] == AgentStatus.ALIVE:
                        updates = {}
                        invalidate_agent_cache = False
                        if row["available_slots"] != available_slots:
                            updates["available_slots"] = available_slots
                        if row["scaling_group"] != sgroup:
                            updates["scaling_group"] = sgroup
                        if row["addr"] != current_addr:
                            updates["addr"] = current_addr
                            invalidate_agent_cache = True
                        if row["public_host"] != agent_info["public_host"]:
                            updates["public_host"] = agent_info["public_host"]
                        if row["public_key"] != agent_info["public_key"]:
                            updates["public_key"] = agent_info["public_key"]
                            invalidate_agent_cache = True
                        if row["version"] != agent_info["version"]:
                            updates["version"] = agent_info["version"]
                        if row["compute_plugins"] != agent_info["compute_plugins"]:
                            updates["compute_plugins"] = agent_info["compute_plugins"]
                        if row["architecture"] != agent_info["architecture"]:
                            updates["architecture"] = agent_info["architecture"]
                        if row["auto_terminate_abusing_kernel"] != auto_terminate_abusing_kernel:
                            updates["auto_terminate_abusing_kernel"] = auto_terminate_abusing_kernel
                        # occupied_slots are updated when kernels starts/terminates
                        if invalidate_agent_cache:
                            self.agent_cache.update(
                                agent_id,
                                current_addr,
                                agent_info["public_key"],
                            )
                        if updates:
                            await self.shared_config.update_resource_slots(slot_key_and_units)
                            update_query = (
                                sa.update(agents).values(updates).where(agents.c.id == agent_id)
                            )
                            await conn.execute(update_query)
                    elif row["status"] in (AgentStatus.LOST, AgentStatus.TERMINATED):
                        await self.shared_config.update_resource_slots(slot_key_and_units)
                        instance_rejoin = True
                        self.agent_cache.update(
                            agent_id,
                            current_addr,
                            agent_info["public_key"],
                        )
                        update_query = (
                            sa.update(agents)
                            .values({
                                "status": AgentStatus.ALIVE,
                                "region": agent_info["region"],
                                "scaling_group": sgroup,
                                "addr": agent_info["addr"],
                                "public_host": agent_info["public_host"],
                                "public_key": agent_info["public_key"],
                                "lost_at": sa.null(),
                                "available_slots": available_slots,
                                "version": agent_info["version"],
                                "compute_plugins": agent_info["compute_plugins"],
                                "architecture": agent_info["architecture"],
                                "auto_terminate_abusing_kernel": auto_terminate_abusing_kernel,
                            })
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
                    try:
                        image_ref = ImageRef(image[0], known_registries, agent_info["architecture"])
                        await pipe.sadd(image_ref.canonical, agent_id)
                    except ValueError:
                        # Skip opaque (non-Backend.AI) image.
                        continue
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
                    sa.select([
                        agents.c.status,
                        agents.c.addr,
                    ])
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
                    .values({
                        "status": status,
                        "status_changed": now,
                        "lost_at": now,
                    })
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
                    params.append({
                        "kernel_id": kernel_id,
                        "last_stat": updates,
                    })
                await conn.execute(update_query, params)

        if per_kernel_updates:
            await execute_with_retry(_update)

    async def sync_agent_kernel_registry(self, agent_id: AgentId) -> None:
        """
        Fetch agent data and status of related kernel data from DB.
        If agent's kernel_registry has unknown kernel data,
        """

        async with self.db.begin_readonly() as db_conn:
            query = (
                sa.select([kernels.c.id, kernels.c.session_id, kernels.c.agent_addr])
                .select_from(kernels)
                .where(
                    (kernels.c.agent == agent_id)
                    & (kernels.c.status.in_(AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                )
            )
            result = await db_conn.execute(query)
            kernel_list = result.fetchall()

        keyfunc = lambda item: item.agent_addr or ""
        for agent_addr, group_iterator in itertools.groupby(
            sorted(kernel_list, key=keyfunc),
            key=keyfunc,
        ):
            grouped_kernels = [*group_iterator]
            aid = grouped_kernels[0].agent
            async with self.agent_cache.rpc_context(
                aid,
            ) as rpc:
                return await rpc.call.sync_kernel_registry([
                    (str(kernel.id), str(kernel.session_id)) for kernel in grouped_kernels
                ])

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

        kern_stat = await redis_helper.execute(
            self.redis_stat,
            lambda r: r.get(str(kernel_id)),
        )

        async def _update_kernel() -> tuple[AccessKey, AgentId] | None:
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
                return kernel.access_key, kernel.agent

        result = await execute_with_retry(_update_kernel)

        if result is None:
            return

        access_key, agent = result

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
        session_id: SessionId,
        reason: str,
    ) -> None:
        new_session_status = await SessionRow.transit_session_status(
            self.db, session_id, status_info=reason
        )
        do_fire_event = new_session_status in (
            SessionStatus.TERMINATED,
            SessionStatus.CANCELLED,
        )
        if do_fire_event:
            await self.event_producer.produce_event(
                SessionTerminatedEvent(session_id, reason),
            )

    async def mark_session_terminating(
        self,
        session_id: SessionId,
        reason: str,
    ) -> None:
        pass

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
        kernel_ids: Sequence[KernelId],
    ) -> Mapping[KernelId, str]:
        async def _pipe_builder(r: Redis):
            pipe = r.pipeline()
            for kernel_id in kernel_ids:
                await pipe.get(f"kernel.{kernel_id}.commit")
            return pipe

        commit_statuses = await redis_helper.execute(self.redis_stat, _pipe_builder)

        return {
            kernel_id: str(result, "utf-8") if result is not None else CommitStatus.READY.value
            for kernel_id, result in zip(kernel_ids, commit_statuses)
        }

    async def commit_session(
        self,
        session: SessionRow,
        new_image_ref: ImageRef,
        *,
        extra_labels: dict[str, str] = {},
    ) -> Mapping[str, Any]:
        """
        Commit a main kernel's container of the given session.
        """

        kernel: KernelRow = session.main_kernel
        if kernel.status != KernelStatus.RUNNING:
            raise InvalidAPIParameters(
                f"Unable to commit since the kernel k:{kernel.id} (of s:{session.id}) is"
                " currently not in RUNNING state."
            )
        email = await self._get_user_email(kernel)
        async with handle_session_exception(self.db, "commit_session", session.id):
            async with self.agent_cache.rpc_context(kernel.agent, order_key=kernel.id) as rpc:
                resp: Mapping[str, Any] = await rpc.call.commit(
                    str(kernel.id),
                    email,
                    canonical=new_image_ref.canonical,
                    extra_labels=extra_labels,
                )
        return resp

    async def push_image(
        self,
        agent: AgentId,
        image_ref: ImageRef,
        registry: ImageRegistry,
    ) -> Mapping[str, Any]:
        """
        Commit a main kernel's container of the given session.
        """
        async with self.agent_cache.rpc_context(agent) as rpc:
            resp: Mapping[str, Any] = await rpc.call.push_image(
                image_ref.canonical,
                image_ref.architecture,
                {**registry, "url": str(registry["url"])},
                is_local=image_ref.is_local,
            )
        return resp

    async def commit_session_to_file(
        self,
        session: SessionRow,
        filename: str | None,
        extra_labels: dict[str, str] = {},
    ) -> Mapping[str, Any]:
        """
        Commit a main kernel's container of the given session.
        """

        kernel: KernelRow = session.main_kernel
        if kernel.status != KernelStatus.RUNNING:
            raise InvalidAPIParameters(
                f"Unable to commit since kernel(id: {kernel.id}) of session(id: {session.id}) is"
                " currently not RUNNING."
            )
        email = await self._get_user_email(kernel)
        now = datetime.now(tzutc()).strftime("%Y-%m-%dT%HH%MM%SS")
        shortend_sname = session.name[:SESSION_NAME_LEN_LIMIT]
        registry, _, filtered = kernel.image.partition("/")
        img_path, _, image_name = filtered.partition("/")
        filename = f"{now}_{shortend_sname}_{image_name}.tar.gz"
        filename = filename.replace(":", "-")
        image_ref = ImageRef(kernel.image, [registry], kernel.architecture)
        async with handle_session_exception(self.db, "commit_session_to_file", session.id):
            async with self.agent_cache.rpc_context(kernel.agent, order_key=kernel.id) as rpc:
                resp: Mapping[str, Any] = await rpc.call.commit(
                    str(kernel.id),
                    email,
                    filename=filename,
                    extra_labels=extra_labels,
                    canonical=image_ref.canonical,
                )
        return resp

    async def get_agent_local_config(
        self,
        agent_id: AgentId,
        agent_addr: str,
    ) -> Mapping[str, str]:
        async with self.agent_cache.rpc_context(agent_id) as rpc:
            return await rpc.call.get_local_config()

    async def get_abusing_report(
        self,
        kernel_id: KernelId,
    ) -> Optional[AbuseReport]:
        hash_name = "abuse_report"
        abusing_report: Optional[dict[str, str]] = await redis_helper.execute(
            self.redis_stat,
            lambda r: r.hgetall(hash_name),
            encoding="utf-8",
        )
        kern_id = str(kernel_id)
        if abusing_report is None or (result := abusing_report.get(kern_id)) is None:
            return None
        return {
            "kernel": kern_id,
            "abuse_report": result,
        }

    async def update_appproxy_endpoint_routes(
        self, db_sess: AsyncSession, endpoint: EndpointRow, active_routes: list[RoutingRow]
    ) -> None:
        target_sessions = await SessionRow.list_sessions(
            db_sess,
            [r.session for r in active_routes],
            kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
        )
        query = (
            sa.select([scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token])
            .select_from(scaling_groups)
            .where((scaling_groups.c.name == endpoint.resource_group))
        )

        result = await db_sess.execute(query)
        sgroup = result.first()
        wsproxy_addr = sgroup["wsproxy_addr"]
        wsproxy_api_token = sgroup["wsproxy_api_token"]

        session_id_to_route_map = {r.session: r for r in active_routes}
        inference_apps: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
        for target_session in target_sessions:
            if target_session.main_kernel.kernel_host is None:
                kernel_host = urlparse(target_session.main_kernel.agent_addr).hostname
            else:
                kernel_host = target_session.main_kernel.kernel_host
            assert kernel_host is not None
            for port_info in target_session.main_kernel.service_ports:
                if not port_info["is_inference"]:
                    continue
                inference_apps[port_info["name"]].append({
                    "session_id": str(target_session.id),
                    "kernel_host": kernel_host,
                    "kernel_port": port_info["host_ports"][0],
                    "traffic_ratio": session_id_to_route_map[target_session.id].traffic_ratio,
                })

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{wsproxy_addr}/v2/endpoints/{endpoint.id}",
                json={
                    "service_name": endpoint.name,
                    "tags": {
                        "session": {
                            "user_uuid": str(endpoint.session_owner),
                            "group_id": str(endpoint.project),
                            "domain_name": endpoint.domain,
                        },
                        "endpoint": {
                            "id": str(endpoint.id),
                            "existing_url": str(endpoint.url) if endpoint.url else None,
                        },
                    },
                    "apps": inference_apps,
                    "open_to_public": endpoint.open_to_public,
                },  # TODO: support for multiple inference apps
                headers={
                    "X-BackendAI-Token": wsproxy_api_token,
                },
            ) as resp:
                endpoint_json = await resp.json()
                async with self.db.begin_session() as db_sess:
                    query = (
                        sa.update(EndpointRow)
                        .values({"url": endpoint_json["endpoint"]})
                        .where(EndpointRow.id == endpoint.id)
                    )
                    await db_sess.execute(query)

    async def delete_appproxy_endpoint(self, db_sess: AsyncSession, endpoint: EndpointRow) -> None:
        query = (
            sa.select([scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token])
            .select_from(scaling_groups)
            .where((scaling_groups.c.name == endpoint.resource_group))
        )

        result = await db_sess.execute(query)
        sgroup = result.first()
        wsproxy_addr = sgroup["wsproxy_addr"]
        wsproxy_api_token = sgroup["wsproxy_api_token"]

        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{wsproxy_addr}/v2/endpoints/{endpoint.id}",
                headers={
                    "X-BackendAI-Token": wsproxy_api_token,
                },
            ):
                pass


async def handle_kernel_creation_lifecycle(
    context: AgentRegistry,
    source: AgentId,
    event: (
        KernelPreparingEvent
        | KernelPullingEvent
        | KernelCreatingEvent
        | KernelStartedEvent
        | KernelCancelledEvent
    ),
) -> None:
    """
    Update the database and perform post_create_kernel() upon
    the events for each step of kernel creation.

    To avoid race condition between consumer and subscriber event handlers,
    we only have this handler to subscribe all kernel creation events,
    but distinguish which one to process using a unique creation_id
    generated when initiating the create_kernels() agent RPC call.
    """
    log.debug(
        "handle_kernel_creation_lifecycle: ev:{} k:{}",
        event.name,
        event.kernel_id,
    )
    if isinstance(event, KernelPreparingEvent):
        # State transition is done by the DoPrepareEvent handler inside the scheduler-distpacher object.
        pass
    elif isinstance(event, KernelPullingEvent):
        await KernelRow.set_kernel_status(
            context.db, event.kernel_id, KernelStatus.PULLING, reason=event.reason
        )
        await SessionRow.set_session_status(context.db, event.session_id, SessionStatus.PULLING)
    elif isinstance(event, KernelCreatingEvent):
        await KernelRow.set_kernel_status(
            context.db, event.kernel_id, KernelStatus.PREPARING, reason=event.reason
        )
    elif isinstance(event, KernelStartedEvent):
        session_id = event.session_id
        await context.finalize_running(event.kernel_id, session_id, event.creation_info)
    elif isinstance(event, KernelCancelledEvent):
        log.warning(f"Kernel cancelled, {event.reason = }")


async def handle_kernel_termination_lifecycle(
    context: AgentRegistry,
    source: AgentId,
    event: KernelTerminatingEvent | KernelTerminatedEvent,
) -> None:
    if isinstance(event, KernelTerminatingEvent):
        # The destroy_kernel() API handler will set the "TERMINATING" status.
        pass
    elif isinstance(event, KernelTerminatedEvent):
        await context.mark_kernel_terminated(event.kernel_id, event.reason, event.exit_code)
        session_id = event.session_id
        await context.check_session_terminated(session_id, event.reason)


async def handle_session_creation_lifecycle(
    context: AgentRegistry,
    source: AgentId,
    event: SessionStartedEvent | SessionCancelledEvent,
) -> None:
    """
    Update the database according to the session-level lifecycle events
    published by the manager.
    """
    if event.creation_id not in context.session_creation_tracker:
        return
    log.debug("handle_session_creation_lifecycle: ev:{} s:{}", event.name, event.session_id)
    if isinstance(event, SessionStartedEvent):
        if tracker := context.session_creation_tracker.get(event.creation_id):
            tracker.set()
    elif isinstance(event, SessionCancelledEvent):
        if tracker := context.session_creation_tracker.get(event.creation_id):
            tracker.set()

    await invoke_session_callback(context, source, event)
    if event.creation_id in context.session_creation_tracker:
        del context.session_creation_tracker[event.creation_id]


async def handle_session_termination_lifecycle(
    context: AgentRegistry,
    agent_id: AgentId,
    event: SessionTerminatingEvent | SessionTerminatedEvent,
) -> None:
    """
    Update the database according to the session-level lifecycle events
    published by the manager.
    """
    if isinstance(event, SessionTerminatingEvent):
        await context.mark_session_terminating(event.session_id, event.reason)
    elif isinstance(event, SessionTerminatedEvent):
        await context.mark_session_terminated(event.session_id, event.reason)

    await invoke_session_callback(context, agent_id, event)


async def handle_destroy_session(
    context: AgentRegistry,
    source: AgentId,
    event: DoTerminateSessionEvent,
) -> None:
    async with context.db.begin_session() as db_sess:
        session = await SessionRow.get_session(
            db_sess, event.session_id, kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS
        )
    await context.destroy_session(
        session,
        forced=False,
        reason=event.reason or KernelLifecycleEventReason.KILLED_BY_EVENT,
    )


async def handle_model_service_status_update(
    context: AgentRegistry,
    source: AgentId,
    event: ModelServiceStatusEvent,
) -> None:
    log.info("HANDLE_MODEL_SERVICE_STATUS_UPDATE (source:{}, event:{})", source, event)
    try:
        async with context.db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                event.session_id,
                allow_stale=False,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
            route = await RoutingRow.get_by_session(db_sess, session.id, load_endpoint=True)
    except SessionNotFound:
        return
    except NoResultFound:
        return

    async def _update():
        async with context.db.begin_session() as db_sess:
            data: dict[str, Any] = {}
            match event.new_status:
                case ModelServiceStatus.HEALTHY:
                    data["status"] = RouteStatus.HEALTHY
                case ModelServiceStatus.UNHEALTHY:
                    data["status"] = RouteStatus.UNHEALTHY
            query = sa.update(RoutingRow).values(data).where(RoutingRow.id == route.id)
            await db_sess.execute(query)

            query = sa.select(RoutingRow).where(
                (RoutingRow.endpoint == route.endpoint) & (RoutingRow.status == RouteStatus.HEALTHY)
            )
            result = await db_sess.execute(query)
            latest_routes = result.fetchall()
            latest_routes = await RoutingRow.list(
                db_sess, route.endpoint, status_filter=[RouteStatus.HEALTHY]
            )

            try:
                await context.update_appproxy_endpoint_routes(
                    db_sess, route.endpoint_row, latest_routes
                )
            except Exception as e:
                if is_db_retry_error(e):
                    raise
                log.exception("failed to communicate with AppProxy endpoint:")

    await execute_with_retry(_update)


async def invoke_session_callback(
    context: AgentRegistry,
    source: AgentId,
    event: (
        SessionEnqueuedEvent
        | SessionScheduledEvent
        | SessionPreparingEvent
        | SessionStartedEvent
        | SessionCancelledEvent
        | SessionTerminatingEvent
        | SessionTerminatedEvent
        | SessionSuccessEvent
        | SessionFailureEvent
    ),
) -> None:
    log.info("INVOKE_SESSION_CALLBACK (source:{}, event:{})", source, event)
    try:
        allow_stale = isinstance(event, (SessionCancelledEvent, SessionTerminatedEvent))
        async with context.db.begin_readonly_session() as db_sess:
            session = await SessionRow.get_session(
                db_sess,
                event.session_id,
                allow_stale=allow_stale,
                kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
            )
    except SessionNotFound:
        return

    try:
        # Update routing status
        # TODO: Check session health
        if session.session_type == SessionTypes.INFERENCE:

            async def _update() -> None:
                new_routes: list[RoutingRow]
                async with context.db.begin_session() as db_sess:
                    route = await RoutingRow.get_by_session(db_sess, session.id, load_endpoint=True)
                    endpoint = await EndpointRow.get(db_sess, route.endpoint, load_routes=True)
                    if isinstance(event, SessionCancelledEvent):
                        update_data: dict[str, Any] = {"status": RouteStatus.FAILED_TO_START}
                        if "error" in session.status_data:
                            if session.status_data["error"]["name"] == "MultiAgentError":
                                errors = session.status_data["error"]["collection"]
                            else:
                                errors = [session.status_data["error"]]
                            update_data["error_data"] = {
                                "type": "session_cancelled",
                                "errors": errors,
                                "session_id": session.id,
                            }
                        query = (
                            sa.update(RoutingRow)
                            .values(update_data)
                            .where(RoutingRow.id == route.id)
                        )
                        await db_sess.execute(query)
                        query = (
                            sa.update(EndpointRow)
                            .values({"retries": endpoint.retries + 1})
                            .where(EndpointRow.id == endpoint.id)
                        )
                        await db_sess.execute(query)
                    elif isinstance(event, SessionTerminatedEvent):
                        query = sa.delete(RoutingRow).where(RoutingRow.id == route.id)
                        await db_sess.execute(query)
                        if endpoint.lifecycle_stage == EndpointLifecycle.CREATED:
                            new_routes = [
                                r
                                for r in endpoint.routings
                                if r.id != route.id and r.status == RouteStatus.HEALTHY
                            ]
                            try:
                                await context.update_appproxy_endpoint_routes(
                                    db_sess, endpoint, new_routes
                                )
                            except Exception as e:
                                if is_db_retry_error(e):
                                    raise
                                log.warning(
                                    "failed to communicate with AppProxy endpoint: {}", str(e)
                                )
                        await db_sess.commit()
                    else:
                        new_route_status: Optional[RouteStatus] = None
                        if isinstance(event, SessionTerminatingEvent):
                            new_route_status = RouteStatus.TERMINATING

                        if new_route_status:
                            query = (
                                sa.update(RoutingRow)
                                .where(RoutingRow.id == route.id)
                                .values({"status": new_route_status})
                            )
                            await db_sess.execute(query)

                            new_routes = [
                                r
                                for r in endpoint.routings
                                if r.id != route.id and r.status == RouteStatus.HEALTHY
                            ]
                            if new_route_status == RouteStatus.HEALTHY:
                                new_routes.append(route)
                            try:
                                await context.update_appproxy_endpoint_routes(
                                    db_sess, endpoint, new_routes
                                )
                            except Exception as e:
                                if is_db_retry_error(e):
                                    raise
                                log.warning(
                                    "failed to communicate with AppProxy endpoint: {}", str(e)
                                )
                        await db_sess.commit()

            await execute_with_retry(_update)

            async def _clear_error() -> None:
                async with context.db.begin_session() as db_sess:
                    route = await RoutingRow.get_by_session(db_sess, session.id, load_endpoint=True)
                    endpoint = await EndpointRow.get(db_sess, route.endpoint, load_routes=True)

                    query = sa.select([sa.func.count("*")]).where(
                        (RoutingRow.endpoint == endpoint.id)
                        & (RoutingRow.status == RouteStatus.HEALTHY)
                    )
                    healthy_routes = await db_sess.scalar(query)
                    if endpoint.desired_session_count == healthy_routes:
                        query = (
                            sa.update(EndpointRow)
                            .where(EndpointRow.id == endpoint.id)
                            .values({"retries": 0})
                        )
                        await db_sess.execute(query)
                        query = sa.delete(RoutingRow).where(
                            (RoutingRow.endpoint == endpoint.id)
                            & (RoutingRow.status == RouteStatus.FAILED_TO_START)
                        )
                        await db_sess.execute(query)

            await execute_with_retry(_clear_error)
    except NoResultFound:
        pass  # Cases when we try to create a inference session for validation (/services/_/try API)
    except Exception:
        log.exception("error while updating route status:")

    if (callback_url := session.callback_url) is None:
        return

    data = {
        "type": "session_lifecycle",
        "event": event.name.removeprefix("session_"),
        "session_id": str(event.session_id),
        "when": datetime.now(tzutc()).isoformat(),
    }

    context.webhook_ptask_group.create_task(
        _make_session_callback(data, callback_url),
    )


async def handle_batch_result(
    context: AgentRegistry,
    source: AgentId,
    event: SessionSuccessEvent | SessionFailureEvent,
) -> None:
    """
    Update the database according to the batch-job completion results
    """
    if isinstance(event, SessionSuccessEvent):
        await SessionRow.set_session_result(context.db, event.session_id, True, event.exit_code)
    elif isinstance(event, SessionFailureEvent):
        await SessionRow.set_session_result(context.db, event.session_id, False, event.exit_code)
    async with context.db.begin_session() as db_sess:
        try:
            session = await SessionRow.get_session(
                db_sess, event.session_id, kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS
            )
        except SessionNotFound:
            return
    await context.destroy_session(
        session,
        reason=KernelLifecycleEventReason.TASK_FINISHED,
    )

    await invoke_session_callback(context, source, event)


async def handle_agent_lifecycle(
    context: AgentRegistry,
    source: AgentId,
    event: AgentStartedEvent | AgentTerminatedEvent,
) -> None:
    if isinstance(event, AgentStartedEvent):
        log.info("instance_lifecycle: ag:{0} joined (via event, {1})", source, event.reason)
        await context.update_instance(
            source,
            {
                "status": AgentStatus.ALIVE,
            },
        )
    if isinstance(event, AgentTerminatedEvent):
        if event.reason == "agent-lost":
            await context.mark_agent_terminated(source, AgentStatus.LOST)
            context.agent_cache.discard(source)
        elif event.reason == "agent-restart":
            log.info("agent@{0} restarting for maintenance.", source)
            await context.update_instance(
                source,
                {
                    "status": AgentStatus.RESTARTING,
                },
            )
        else:
            # On normal instance termination, kernel_terminated events were already
            # triggered by the agent.
            await context.mark_agent_terminated(source, AgentStatus.TERMINATED)
            context.agent_cache.discard(source)


async def handle_agent_heartbeat(
    context: AgentRegistry,
    source: AgentId,
    event: AgentHeartbeatEvent,
) -> None:
    await context.handle_heartbeat(source, event.agent_info)


async def handle_route_creation(
    context: AgentRegistry,
    source: AgentId,
    event: RouteCreatedEvent,
) -> None:
    endpoint: EndpointRow | None = None

    try:
        async with context.db.begin_readonly_session() as db_sess:
            log.debug("Route ID: {}", event.route_id)
            route = await RoutingRow.get(db_sess, event.route_id)
            endpoint = await EndpointRow.get(db_sess, route.endpoint, load_image=True)

            query = sa.select(sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)).where(
                UserRow.uuid == endpoint.created_user
            )
            created_user = (await db_sess.execute(query)).fetchone()
            if endpoint.session_owner != endpoint.created_user:
                query = sa.select(
                    sa.join(UserRow, KeyPairRow, KeyPairRow.user == UserRow.uuid)
                ).where(UserRow.uuid == endpoint.session_owner)
                session_owner = (await db_sess.execute(query)).fetchone()
            else:
                session_owner = created_user

            _, group_id, resource_policy = await query_userinfo(
                db_sess,
                created_user.uuid,
                created_user["access_key"],
                created_user.role,
                created_user.domain_name,
                None,
                endpoint.domain,
                endpoint.project,
                query_on_behalf_of=session_owner["access_key"],
            )

            await context.create_session(
                f"{endpoint.name}-{str(event.route_id)}",
                endpoint.image_row.name,
                endpoint.image_row.architecture,
                UserScope(
                    domain_name=endpoint.domain,
                    group_id=group_id,
                    user_uuid=session_owner["uuid"],
                    user_role=session_owner["role"],
                ),
                session_owner["access_key"],
                resource_policy,
                SessionTypes.INFERENCE,
                {
                    "mounts": [endpoint.model, *[m.vfid.folder_id for m in endpoint.extra_mounts]],
                    "mount_map": {
                        endpoint.model: endpoint.model_mount_destination,
                        **{
                            m.vfid.folder_id: m.kernel_path.as_posix()
                            for m in endpoint.extra_mounts
                        },
                    },
                    "mount_options": {
                        m.vfid.folder_id: {"permission": m.mount_perm}
                        for m in endpoint.extra_mounts
                    },
                    "model_definition_path": endpoint.model_definition_path,
                    "runtime_variant": endpoint.runtime_variant.value,
                    "environ": endpoint.environ,
                    "scaling_group": endpoint.resource_group,
                    "resources": endpoint.resource_slots,
                    "resource_opts": endpoint.resource_opts,
                    "preopen_ports": None,
                    "agent_list": None,
                },
                ClusterMode[endpoint.cluster_mode],
                endpoint.cluster_size,
                bootstrap_script=endpoint.bootstrap_script,
                startup_command=endpoint.startup_command,
                tag=endpoint.tag,
                callback_url=endpoint.callback_url,
                enqueue_only=True,
                route_id=route.id,
                sudo_session_enabled=session_owner.sudo_session_enabled,
            )
    except Exception as e:
        log.exception("error while creating session:")
        error_data = {
            "type": "creation_failed",
            "errors": [
                {
                    "src": "",
                    "name": e.__class__.__name__,
                    "repr": e.__repr__(),
                }
            ],
        }

        async def _update():
            async with context.db.begin_session() as db_sess:
                query = (
                    sa.update(RoutingRow)
                    .values({"status": RouteStatus.FAILED_TO_START, "error_data": error_data})
                    .where(RoutingRow.id == event.route_id)
                )
                await db_sess.execute(query)
                if endpoint:
                    query = (
                        sa.update(EndpointRow)
                        .values({"retries": endpoint.retries + 1})
                        .where(EndpointRow.id == endpoint.id)
                    )
                    await db_sess.execute(query)

        await execute_with_retry(_update)


async def handle_check_agent_resource(
    context: AgentRegistry, source: AgentId, event: DoAgentResourceCheckEvent
) -> None:
    async with context.db.begin_readonly() as conn:
        query = (
            sa.select([agents.c.occupied_slots]).select_from(agents).where(agents.c.id == source)
        )
        result = await conn.execute(query)
        row = result.first()
        if not row:
            raise InstanceNotFound(source)
        log.info("agent@{0} occupied slots: {1}", source, row["occupied_slots"].to_json())


async def check_scaling_group(
    conn: SAConnection,
    scaling_group: str | None,
    session_type: SessionTypes,
    access_key: AccessKey,
    domain_name: str,
    group_id: Union[uuid.UUID, str],
    public_sgroup_only: bool = False,
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
    if public_sgroup_only:
        candidates = [sgroup for sgroup in candidates if sgroup["is_public"]]
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


async def handle_kernel_log(
    context: AgentRegistry,
    source: AgentId,
    event: DoSyncKernelLogsEvent,
) -> None:
    # The log data is at most 10 MiB.
    log_buffer = BytesIO()
    log_key = f"containerlog.{event.container_id}"
    try:
        list_size = await redis_helper.execute(
            context.redis_stream,
            lambda r: r.llen(log_key),
        )
        if list_size is None:
            # The log data is expired due to a very slow event delivery.
            # (should never happen!)
            log.warning(
                "tried to store console logs for cid:{}, but the data is expired",
                event.container_id,
            )
            return
        for _ in range(list_size):
            # Read chunk-by-chunk to allow interleaving with other Redis operations.
            chunk = await redis_helper.execute(context.redis_stream, lambda r: r.lpop(log_key))
            if chunk is None:  # maybe missing
                log_buffer.write(b"(container log unavailable)\n")
                break
            log_buffer.write(chunk)
        try:
            log_data = log_buffer.getvalue()

            async def _update_log() -> None:
                async with context.db.begin() as conn:
                    update_query = (
                        sa.update(kernels)
                        .values(container_log=log_data)
                        .where(kernels.c.id == event.kernel_id)
                    )
                    await conn.execute(update_query)

            await execute_with_retry(_update_log)
        finally:
            # Clear the log data from Redis when done.
            await redis_helper.execute(
                context.redis_stream,
                lambda r: r.delete(log_key),
            )
    finally:
        log_buffer.close()


async def _make_session_callback(data: dict[str, Any], url: yarl.URL) -> None:
    log_func = log.info
    log_msg: str = ""
    log_fmt: str = ""
    log_arg: Any = None
    begin = time.monotonic()
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30.0),
        ) as session:
            try:
                async with session.post(url, json=data) as response:
                    if response.content_length is not None and response.content_length > 0:
                        log_func = log.warning
                        log_msg = "warning"
                        log_fmt = (
                            "{3[0]} {3[1]} - the callback response body was not empty! "
                            "(len: {3[2]:,} bytes)"
                        )
                        log_arg = (response.status, response.reason, response.content_length)
                    else:
                        log_msg = "result"
                        log_fmt = "{3[0]} {3[1]}"
                        log_arg = (response.status, response.reason)
            except aiohttp.ClientError as e:
                log_func = log.warning
                log_msg, log_fmt, log_arg = "failed", "{3}", repr(e)
    except asyncio.CancelledError:
        log_func = log.warning
        log_msg, log_fmt, log_arg = "cancelled", "elapsed_time = {3:.6f}", time.monotonic() - begin
    except asyncio.TimeoutError:
        log_func = log.warning
        log_msg, log_fmt, log_arg = "timeout", "elapsed_time = {3:.6f}", time.monotonic() - begin
    finally:
        log_func(
            "Session lifecycle callback " + log_msg + " (e:{0}, s:{1}, url:{2}): " + log_fmt,
            data["event"],
            data["session_id"],
            url,
            log_arg,
        )
