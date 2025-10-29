from __future__ import annotations

import asyncio
import base64
import copy
import itertools
import json
import logging
import re
import secrets
import time
import uuid
from collections import defaultdict
from collections.abc import (
    Iterable,
    Mapping,
    MutableMapping,
    Sequence,
)
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    TypeAlias,
    Union,
    cast,
)

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
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload, selectinload
from sqlalchemy.orm.exc import NoResultFound
from typeguard import check_type
from yarl import URL

from ai.backend.common.asyncio import cancel_tasks
from ai.backend.common.auth import PublicKey, SecretKey
from ai.backend.common.clients.http_client.client_pool import (
    ClientKey,
    ClientPool,
    tcp_client_session_factory,
)
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.config import ModelHealthCheck
from ai.backend.common.defs.session import SESSION_PRIORITY_DEFAULT
from ai.backend.common.docker import ImageRef, LabelName
from ai.backend.common.dto.agent.response import CodeCompletionResp, PurgeImageResp, PurgeImagesResp
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.agent.anycast import (
    AgentImagesRemoveEvent,
    AgentStartedEvent,
    AgentTerminatedEvent,
    DoAgentResourceCheckEvent,
)
from ai.backend.common.events.event_types.image.anycast import (
    ImagePullFailedEvent,
    ImagePullFinishedEvent,
    ImagePullStartedEvent,
)
from ai.backend.common.events.event_types.kernel.anycast import (
    KernelCancelledAnycastEvent,
    KernelCreatingAnycastEvent,
    KernelHeartbeatEvent,
    KernelPreparingAnycastEvent,
    KernelPullingAnycastEvent,
    KernelStartedAnycastEvent,
    KernelTerminatedAnycastEvent,
    KernelTerminatingAnycastEvent,
)
from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.events.event_types.model_serving.anycast import (
    EndpointRouteListUpdatedEvent,
    ModelServiceStatusAnycastEvent,
    RouteCreatedAnycastEvent,
)
from ai.backend.common.events.event_types.session.anycast import (
    DoTerminateSessionEvent,
    SessionCancelledAnycastEvent,
    SessionEnqueuedAnycastEvent,
    SessionFailureAnycastEvent,
    SessionPreparingAnycastEvent,
    SessionScheduledAnycastEvent,
    SessionStartedAnycastEvent,
    SessionSuccessAnycastEvent,
    SessionTerminatedAnycastEvent,
    SessionTerminatingAnycastEvent,
)
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
    SessionCancelledBroadcastEvent,
    SessionEnqueuedBroadcastEvent,
    SessionStartedBroadcastEvent,
    SessionTerminatingBroadcastEvent,
)
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.events.hub.propagators.cache import WithCachePropagator
from ai.backend.common.events.types import EventCacheDomain, EventDomain
from ai.backend.common.exception import AliasResolutionFailed, BackendAIError
from ai.backend.common.plugin.hook import ALL_COMPLETED, PASSED, HookPluginContext
from ai.backend.common.service_ports import parse_service_ports
from ai.backend.common.types import (
    MODEL_SERVICE_RUNTIME_PROFILES,
    AbuseReport,
    AccessKey,
    AgentId,
    AutoPullBehavior,
    BinarySize,
    ClusterInfo,
    ClusterMode,
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
    CommitStatus,
    ContainerKernelId,
    DeviceId,
    HardwareMetadata,
    ImageAlias,
    ImageConfig,
    ImageRegistry,
    KernelCreationConfig,
    KernelEnqueueingConfig,
    KernelId,
    ModelServiceStatus,
    ResourceSlot,
    RuntimeVariant,
    SessionEnqueueingConfig,
    SessionId,
    SessionTypes,
    SlotName,
)
from ai.backend.common.utils import str_to_timedelta
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.wsproxy.types import (
    CreateEndpointRequestBody,
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.endpoint import ModelServiceHelper
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.scheduler.types.session_creation import SessionCreationSpec
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.utils import query_userinfo

from .agent_cache import AgentRPCCache
from .clients.agent.client import AgentClient
from .clients.wsproxy.client import AppProxyClient
from .defs import DEFAULT_IMAGE_ARCH, DEFAULT_ROLE, DEFAULT_SHARED_MEMORY_SIZE, INTRINSIC_SLOTS
from .errors.api import InvalidAPIParameters
from .errors.common import GenericForbidden, RejectedByHook
from .errors.image import ImageNotFound
from .errors.kernel import (
    QuotaExceeded,
    SessionAlreadyExists,
    SessionNotFound,
    TooManySessionsMatched,
)
from .errors.resource import InstanceNotFound, ScalingGroupNotFound
from .exceptions import MultiAgentError
from .models import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    AGENT_RESOURCE_OCCUPYING_SESSION_STATUSES,
    ALLOWED_IMAGE_ROLES_FOR_SESSION_TYPE,
    PRIVATE_SESSION_TYPES,
    USER_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    USER_RESOURCE_OCCUPYING_SESSION_STATUSES,
    AgentRow,
    EndpointRow,
    ImageRow,
    KernelLoadingStrategy,
    KernelRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    NetworkRow,
    NetworkType,
    RouteStatus,
    RoutingRow,
    ScalingGroupRow,
    SessionDependencyRow,
    SessionRow,
    UserRole,
    UserRow,
    VFolderRow,
    agents,
    domains,
    handle_session_exception,
    kernels,
    prepare_dotfiles,
    prepare_vfolder_mounts,
    query_allowed_sgroups,
    query_bootstrap_script,
    scaling_groups,
    verify_vfolder_name,
)
from .models.container_registry import ContainerRegistryRow
from .models.image import bulk_get_image_configs
from .models.session import (
    SESSION_KERNEL_STATUS_MAPPING,
    ConcurrencyUsed,
    SessionLifecycleManager,
)
from .models.storage import StorageSessionManager
from .models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
    execute_with_txn_retry,
    reenter_txn_session,
    sql_json_merge,
)
from .scheduler.types import AgentAllocationContext, KernelAgentBinding, SchedulingContext
from .types import UserScope

MSetType: TypeAlias = Mapping[Union[str, bytes], Union[bytes, float, int, str]]
__all__ = ["AgentRegistry", "InstanceNotFound"]

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

SESSION_NAME_LEN_LIMIT = 10
DEFAULT_WAIT_TIMEOUT_SECONDS = 60


class AgentRegistry:
    """
    Provide a high-level API to create, destroy, and query the computation
    kernels.

    The registry is also responsible to implement our resource management
    policy, such as the limitation of maximum number of kernels per instance.
    """

    _kernel_actual_allocated_resources: dict[KernelId, ResourceSlot]
    _scheduling_controller: SchedulingController
    _use_sokovan: bool
    _event_hub: EventHub

    session_creation_tracker: dict[str, asyncio.Event]
    pending_waits: set[asyncio.Task[None]]
    database_ptask_group: aiotools.PersistentTaskGroup
    webhook_ptask_group: aiotools.PersistentTaskGroup
    _client_pool: ClientPool

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        db: ExtendedAsyncSAEngine,
        agent_cache: AgentRPCCache,
        valkey_stat: ValkeyStatClient,
        valkey_live: ValkeyLiveClient,
        valkey_image: ValkeyImageClient,
        event_producer: EventProducer,
        event_hub: EventHub,
        storage_manager: StorageSessionManager,
        hook_plugin_ctx: HookPluginContext,
        network_plugin_ctx: NetworkPluginContext,
        scheduling_controller: SchedulingController,
        *,
        debug: bool = False,
        manager_public_key: PublicKey,
        manager_secret_key: SecretKey,
        use_sokovan: bool = True,
    ) -> None:
        self.config_provider = config_provider
        self.docker = aiodocker.Docker()
        self.db = db
        self.agent_cache = agent_cache
        self.valkey_stat = valkey_stat
        self.valkey_live = valkey_live
        self.valkey_image = valkey_image
        self.event_producer = event_producer
        self._event_hub = event_hub
        self.storage_manager = storage_manager
        self.hook_plugin_ctx = hook_plugin_ctx
        self.network_plugin_ctx = network_plugin_ctx
        self._kernel_actual_allocated_resources = {}
        self._scheduling_controller = scheduling_controller
        self._use_sokovan = use_sokovan
        self.debug = debug
        self.rpc_keepalive_timeout = int(config_provider.config.network.rpc.keepalive_timeout)
        self.rpc_auth_manager_public_key = manager_public_key
        self.rpc_auth_manager_secret_key = manager_secret_key
        self.session_lifecycle_mgr = SessionLifecycleManager(
            db,
            valkey_stat,
            valkey_live,
            event_producer,
            hook_plugin_ctx,
            self,
        )
        self._client_pool = ClientPool(tcp_client_session_factory)

    def _get_agent_client(
        self,
        agent_id: AgentId,
        *,
        invoke_timeout: Optional[float] = None,
        order_key: Optional[str] = None,
    ) -> AgentClient:
        """Get an AgentClient for the given agent ID.

        Args:
            agent_id: The agent ID to get the client for

        Returns:
            AgentClient instance for the agent
        """
        # TODO: Apply AgentClient Pool
        return AgentClient(
            self.agent_cache,
            agent_id,
            invoke_timeout=invoke_timeout,
            order_key=order_key,
        )

    async def init(self) -> None:
        self.heartbeat_lock = asyncio.Lock()
        self.session_creation_tracker = {}
        self.pending_waits = set()
        self.database_ptask_group = aiotools.PersistentTaskGroup()
        self.webhook_ptask_group = aiotools.PersistentTaskGroup()

    async def shutdown(self) -> None:
        await cancel_tasks(self.pending_waits)
        await self.database_ptask_group.shutdown()
        await self.webhook_ptask_group.shutdown()

    def _load_app_proxy_client(self, address: str, token: str) -> AppProxyClient:
        client_session = self._client_pool.load_client_session(
            ClientKey(
                endpoint=address,
                domain="wsproxy",
            )
        )
        return AppProxyClient(client_session, address, token)

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
        agent_client = self._get_agent_client(agent["id"])
        result = await agent_client.gather_hwinfo()
        return {k: check_type(v, HardwareMetadata) for k, v in result.items()}

    async def gather_storage_hwinfo(self, vfolder_host: str) -> HardwareMetadata:
        proxy_name, volume_name = self.storage_manager.get_proxy_and_volume(vfolder_host)
        manager_client = self.storage_manager.get_manager_facing_client(proxy_name)
        result = await manager_client.get_volume_hwinfo(volume_name)
        return check_type(result, HardwareMetadata)

    async def scan_gpu_alloc_map(self, instance_id: AgentId) -> Mapping[str, Any]:
        agent = await self.get_instance(instance_id, agents.c.addr)
        agent_client = self._get_agent_client(agent["id"])
        return await agent_client.scan_gpu_alloc_map()

    async def _wait_for_session_running(
        self,
        session_id: SessionId,
        propagator: WithCachePropagator,
        max_wait: int,
    ) -> None:
        cache_id = EventCacheDomain.SESSION_SCHEDULER.cache_id(str(session_id))
        while True:
            try:
                with _timeout(DEFAULT_WAIT_TIMEOUT_SECONDS):
                    async for event in propagator.receive(cache_id):
                        if isinstance(event, SchedulingBroadcastEvent):
                            if event.status_transition == str(SessionStatus.RUNNING):
                                return
                            if event.status_transition in (
                                str(SessionStatus.TERMINATED),
                                str(SessionStatus.CANCELLED),
                            ):
                                raise SessionNotFound("Session terminated during scheduling")
            except asyncio.TimeoutError as e:
                if max_wait > 0:
                    raise e
                async with self.db.begin_readonly_session() as db_session:
                    query = sa.select(SessionRow.status).where(SessionRow.id == session_id)
                    result = await db_session.execute(query)
                    row = result.first()

                    if row is None:
                        raise SessionNotFound(f"Session {session_id} not found")

                    if row.status == SessionStatus.RUNNING:
                        return
                    elif row.status in (SessionStatus.TERMINATED, SessionStatus.CANCELLED):
                        raise SessionNotFound("Session terminated during scheduling")

    async def create_session(
        self,
        session_name: str,
        image_ref: ImageRef,
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
        priority: int = SESSION_PRIORITY_DEFAULT,
        bootstrap_script: Optional[str] = None,
        dependencies: Optional[List[uuid.UUID]] = None,
        startup_command: Optional[str] = None,
        starts_at_timestamp: Optional[str] = None,
        batch_timeout: Optional[timedelta] = None,
        tag: Optional[str] = None,
        callback_url: Optional[yarl.URL] = None,
        route_id: Optional[uuid.UUID] = None,
        sudo_session_enabled: bool = False,
    ) -> Mapping[str, Any]:
        log.debug("create_session():")
        resp: MutableMapping[str, Any] = {}

        current_task = asyncio.current_task()
        assert current_task is not None

        mount_id_map = config.get("mount_id_map")
        mount_map = config.get("mount_map")
        if mount_id_map is None:
            mount_id_map = {}
        if mount_map is None:
            mount_map = {}

        combined_mount_map = {**mount_map, **mount_id_map}

        # Check work directory and reserved name directory.
        original_folders = combined_mount_map.keys()
        alias_folders = combined_mount_map.values()
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
            available_resource_slots = (
                await self.config_provider.legacy_etcd_config_loader.get_resource_slots()
            )
            try:
                ResourceSlot.from_user_input(_resources, available_resource_slots)
            except ValueError as e:
                raise InvalidAPIParameters(f"Invalid resource allocation: {e}")

        # Resolve the image reference.
        try:
            async with self.db.begin_readonly_session() as session:
                image_row = await ImageRow.resolve(
                    session,
                    [image_ref],
                )
            if (
                _owner_id := image_row.labels.get("ai.backend.customized-image.owner")
            ) and _owner_id != f"user:{user_scope.user_uuid}":
                raise ImageNotFound
            if not image_ref.is_local:
                async with self.db.begin_readonly() as conn:
                    query = (
                        sa.select([domains.c.allowed_docker_registries])
                        .select_from(domains)
                        .where(domains.c.name == user_scope.domain_name)
                    )
                    allowed_registries = await conn.scalar(query)
                    if image_ref.registry not in allowed_registries:
                        raise AliasResolutionFailed
        except AliasResolutionFailed:
            raise ImageNotFound("unknown alias or disallowed registry")

        # Check existing (access_key, session_name) instance
        try:
            # NOTE: We can reuse the session IDs of TERMINATED sessions only.
            # NOTE: Reusing a session in the PENDING status returns an empty value in service_ports.
            async with self.db.begin_readonly_session() as db_session:
                sess = await SessionRow.get_session(
                    db_session,
                    session_name,
                    owner_access_key,
                    kernel_loading_strategy=KernelLoadingStrategy.MAIN_KERNEL_ONLY,
                )
                running_image_ref = (
                    await ImageRow.resolve(
                        db_session,
                        [
                            ImageIdentifier(sess.main_kernel.image, sess.main_kernel.architecture),
                        ],
                    )
                ).image_ref
            if running_image_ref != image_ref:
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
                "service_ports": sess.main_kernel.service_ports,  # deprecated, left for compatibility.
                "servicePorts": sess.main_kernel.service_ports,
                "created": False,
            }
        except SessionNotFound:
            # It's time to create a new session.
            pass

        if session_type == SessionTypes.BATCH and not startup_command:
            raise InvalidAPIParameters("Batch sessions must have a non-empty startup command.")
        if session_type != SessionTypes.BATCH:
            if starts_at_timestamp:
                raise InvalidAPIParameters(
                    "Parameter starts_at should be used only for batch sessions"
                )
            if batch_timeout is not None:
                raise InvalidAPIParameters(
                    "Parameter batch_timeout should be used only for batch sessions"
                )

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

        async with self.db.begin_readonly_session() as db_session:
            conn = await db_session.connection()
            assert conn
            # check if network exists
            if _network_id := config.get("attach_network"):
                network = await NetworkRow.get(db_session, _network_id)
            else:
                network = None

            # Use keypair bootstrap_script if it is not delivered as a parameter
            if not bootstrap_script:
                script, _ = await query_bootstrap_script(conn, owner_access_key)
                bootstrap_script = script

            user_row = await db_session.scalar(
                sa.select(UserRow).where(UserRow.uuid == user_scope.user_uuid)
            )
            user_row = cast(UserRow, user_row)

        public_sgroup_only = session_type not in PRIVATE_SESSION_TYPES
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
                                    "uid": user_row.container_uid,
                                    "main_gid": user_row.container_main_gid,
                                    "supplementary_gids": (user_row.container_gids or []),
                                    "image_ref": image_ref,
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
                        priority=priority,
                        cluster_mode=cluster_mode,
                        cluster_size=cluster_size,
                        session_tag=tag,
                        starts_at=starts_at,
                        batch_timeout=batch_timeout,
                        agent_list=config["agent_list"],
                        dependency_sessions=[SessionId(d) for d in dependencies],
                        callback_url=callback_url,
                        public_sgroup_only=public_sgroup_only,
                        route_id=route_id,
                        sudo_session_enabled=sudo_session_enabled,
                        network=network,
                    )
                ),
            )

            resp["sessionId"] = str(session_id)  # changed since API v5
            resp["sessionName"] = str(session_name)
            resp["status"] = "PENDING"
            resp["servicePorts"] = []
            resp["created"] = True

            if not enqueue_only:
                # Create and register propagator for event hub
                # Create event fetcher and cache propagator
                event_fetcher = EventFetcher(self.event_producer._msg_queue)
                propagator = WithCachePropagator(event_fetcher)
                self.pending_waits.add(current_task)
                max_wait = max_wait_seconds

                # Register propagator and ensure cleanup
                self._event_hub.register_event_propagator(
                    propagator, [(EventDomain.SESSION, str(session_id))]
                )
                try:
                    await self._wait_for_session_running(session_id, propagator, max_wait)
                except asyncio.TimeoutError:
                    resp["status"] = "TIMEOUT"
                else:
                    await asyncio.sleep(0.5)
                    async with self.db.begin_readonly_session() as db_session:
                        query = sa.select(KernelRow.status, KernelRow.service_ports).where(
                            (KernelRow.session_id == session_id)
                            & (KernelRow.cluster_role == DEFAULT_ROLE)
                        )
                        result = await db_session.execute(query)
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
                finally:
                    # Always unregister propagator
                    self._event_hub.unregister_event_propagator(propagator.id())
            return resp
        except asyncio.CancelledError:
            raise
        finally:
            self.pending_waits.discard(current_task)
            # Clean up old tracker if exists (for backward compatibility)
            if session_creation_id in self.session_creation_tracker:
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
        attach_network: uuid.UUID | None = None,
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
                    # TODO: Rename this to `mounts`
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
                        f"{proto}://{credential['username']}:{credential['password']}@{url}"
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
                            ImageIdentifier(kernel_config["image"], kernel_config["architecture"]),
                            ImageAlias(kernel_config["image"]),
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
                    check_type(kernel_config, KernelEnqueueingConfig),  # type: ignore
                )

        session_creation_id = secrets.token_urlsafe(16)
        kernel_id: Optional[KernelId] = None
        current_task = asyncio.current_task()
        assert current_task is not None

        if attach_network:
            async with self.db.begin_readonly_session() as db_sess:
                network = await NetworkRow.get(db_sess, attach_network)
        else:
            network = None
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
                        network=network,
                    ),
                )
            )
            kernel_id = cast(KernelId, session_id)  # the main kernel's ID is the session ID.
            resp["kernelId"] = str(kernel_id)
            resp["status"] = "PENDING"
            resp["servicePorts"] = []
            resp["created"] = True

            if not enqueue_only:
                # Create and register propagator for event hub
                # Create event fetcher and cache propagator
                event_fetcher = EventFetcher(self.event_producer._msg_queue)
                propagator = WithCachePropagator(event_fetcher)
                self.pending_waits.add(current_task)
                max_wait = max_wait_seconds

                # Register propagator and ensure cleanup
                self._event_hub.register_event_propagator(
                    propagator, [(EventDomain.SESSION, str(session_id))]
                )
                try:
                    await self._wait_for_session_running(session_id, propagator, max_wait)
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
                finally:
                    # Always unregister propagator
                    self._event_hub.unregister_event_propagator(propagator.id())
            return resp
        except asyncio.CancelledError:
            raise
        finally:
            self.pending_waits.discard(current_task)
            # Clean up old tracker if exists (for backward compatibility)
            if session_creation_id in self.session_creation_tracker:
                del self.session_creation_tracker[session_creation_id]

    async def _enqueue_session_via_sokovan(
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
        priority: int,
        public_sgroup_only: bool,
        cluster_mode: ClusterMode,
        cluster_size: int,
        session_tag: Optional[str],
        internal_data: Optional[dict],
        starts_at: Optional[datetime],
        batch_timeout: Optional[timedelta],
        agent_list: Optional[Sequence[str]],
        dependency_sessions: Optional[Sequence[SessionId]],
        callback_url: Optional[URL],
        route_id: Optional[uuid.UUID],
        sudo_session_enabled: bool,
        network: NetworkRow | None,
    ) -> SessionId:
        """Enqueue session using Sokovan scheduling controller."""
        kernel_enqueue_configs: List[KernelEnqueueingConfig] = session_enqueue_configs[
            "kernel_configs"
        ]

        # Create SessionCreationSpec
        spec = SessionCreationSpec(
            session_creation_id=session_creation_id,
            session_name=session_name,
            access_key=access_key,
            user_scope=user_scope,
            session_type=session_type,
            cluster_mode=cluster_mode,
            cluster_size=cluster_size,
            priority=priority,
            resource_policy=resource_policy,
            kernel_specs=kernel_enqueue_configs,
            creation_spec=session_enqueue_configs["creation_config"],
            scaling_group=scaling_group,
            session_tag=session_tag,
            starts_at=starts_at,
            batch_timeout=batch_timeout,
            dependency_sessions=list(dependency_sessions) if dependency_sessions else None,
            callback_url=callback_url,
            route_id=route_id,
            sudo_session_enabled=sudo_session_enabled,
            network=network,
            designated_agent_list=list(agent_list) if agent_list else None,
            internal_data=internal_data,
            public_sgroup_only=public_sgroup_only,
        )

        # Delegate to scheduling controller
        return await self._scheduling_controller.enqueue_session(spec)

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
        priority: int = SESSION_PRIORITY_DEFAULT,
        public_sgroup_only: bool = True,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        cluster_size: int = 1,
        session_tag: Optional[str] = None,
        internal_data: Optional[dict] = None,
        starts_at: Optional[datetime] = None,
        batch_timeout: Optional[timedelta] = None,
        agent_list: Optional[Sequence[str]] = None,
        dependency_sessions: Optional[Sequence[SessionId]] = None,
        callback_url: Optional[URL] = None,
        route_id: Optional[uuid.UUID] = None,
        sudo_session_enabled: bool = False,
        network: NetworkRow | None = None,
    ) -> SessionId:
        # Use sokovan scheduling controller if enabled
        if self._use_sokovan:
            return await self._enqueue_session_via_sokovan(
                session_creation_id=session_creation_id,
                session_name=session_name,
                access_key=access_key,
                session_enqueue_configs=session_enqueue_configs,
                scaling_group=scaling_group,
                session_type=session_type,
                resource_policy=resource_policy,
                user_scope=user_scope,
                priority=priority,
                public_sgroup_only=public_sgroup_only,
                cluster_mode=cluster_mode,
                cluster_size=cluster_size,
                session_tag=session_tag,
                internal_data=internal_data,
                starts_at=starts_at,
                batch_timeout=batch_timeout,
                agent_list=agent_list,
                dependency_sessions=dependency_sessions,
                callback_url=callback_url,
                route_id=route_id,
                sudo_session_enabled=sudo_session_enabled,
                network=network,
            )

        # Original implementation
        session_id = SessionId(uuid.uuid4())

        kernel_enqueue_configs = session_enqueue_configs["kernel_configs"]
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

        async with self.db.begin_readonly_session() as sess:
            conn = await sess.connection()
            assert conn
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

            scaling_group_query = sa.select(ScalingGroupRow).where(
                ScalingGroupRow.name == checked_scaling_group
            )
            scaling_group_query_result = await sess.execute(scaling_group_query)
            scaling_group_row: ScalingGroupRow = scaling_group_query_result.scalar()

            # Translate mounts (mount_ids) / mount_map (mount_id_map) / mount_options into vfolder mounts
            requested_mounts = session_enqueue_configs["creation_config"].get("mounts") or []
            requested_mount_ids = session_enqueue_configs["creation_config"].get("mount_ids") or []
            requested_mount_map = session_enqueue_configs["creation_config"].get("mount_map") or {}
            requested_mount_id_map = (
                session_enqueue_configs["creation_config"].get("mount_id_map") or {}
            )

            requested_mount_options = (
                session_enqueue_configs["creation_config"].get("mount_options") or {}
            )
            allowed_vfolder_types = (
                await self.config_provider.legacy_etcd_config_loader.get_vfolder_types()
            )

            combined_mounts = requested_mounts + requested_mount_ids
            combined_mount_map = {**requested_mount_map, **requested_mount_id_map}

            vfolder_mounts = await prepare_vfolder_mounts(
                conn,
                self.storage_manager,
                allowed_vfolder_types,
                user_scope,
                resource_policy,
                combined_mounts,
                combined_mount_map,
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
            "priority": priority,
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
            "batch_timeout": int(batch_timeout.total_seconds())
            if batch_timeout is not None
            else None,
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
            "mounts": [*{mount.name for mount in vfolder_mounts}],  # TODO: keep for legacy?
            "vfolder_mounts": vfolder_mounts,
            "repl_in_port": 0,
            "repl_out_port": 0,
            "stdin_port": 0,
            "stdout_port": 0,
            "preopen_ports": sa.bindparam("preopen_ports"),
            "use_host_network": scaling_group_row.use_host_network,
        }

        if network:
            session_data["network_type"] = NetworkType.PERSISTENT
            session_data["network_id"] = str(network.id)
        elif scaling_group_row.use_host_network:
            session_data["network_type"] = NetworkType.HOST
        else:
            session_data["network_type"] = NetworkType.VOLATILE

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
            image_min_slots = await image_row.get_min_slot(
                self.config_provider.legacy_etcd_config_loader
            )
            known_slot_types = (
                await self.config_provider.legacy_etcd_config_loader.get_resource_slots()
            )

            labels = cast(dict, image_row.labels)

            # Check if the image is available for a given session type.
            if (_img_role := labels.get("ai.backend.role")) is not None:
                if _img_role not in ALLOWED_IMAGE_ROLES_FOR_SESSION_TYPE[session_type]:
                    raise InvalidAPIParameters(
                        f"Cannot create {session_type} session with the given image. (img:"
                        f" {image_ref.name}, img role: {_img_role})"
                    )

            # Parse service ports to check for port errors
            service_ports = parse_service_ports(
                labels.get("ai.backend.service-ports", ""),
                labels.get("ai.backend.endpoint-ports", ""),
                BackendAIError,
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
            raw_shmem: Optional[str] = resource_opts.get("shmem")
            if raw_shmem is None:
                raw_shmem = labels.get("ai.backend.resource.preferred.shmem")
            if not raw_shmem:
                # raw_shmem is None or empty string ("")
                raw_shmem = DEFAULT_SHARED_MEMORY_SIZE
            try:
                shmem = BinarySize.from_str(raw_shmem)
            except ValueError:
                log.warning(
                    f"Failed to convert raw `shmem({raw_shmem})` "
                    f"to a decimal value. Fallback to default({DEFAULT_SHARED_MEMORY_SIZE})."
                )
                shmem = BinarySize.from_str(DEFAULT_SHARED_MEMORY_SIZE)
            allow_fractional_resource_fragmentation = resource_opts.get(
                "allow_fractional_resource_fragmentation"
            )
            if allow_fractional_resource_fragmentation is None:
                allow_fractional_resource_fragmentation = (
                    scaling_group_row.scheduler_opts.allow_fractional_resource_fragmentation
                )
            resource_opts["allow_fractional_resource_fragmentation"] = (
                allow_fractional_resource_fragmentation
            )
            resource_opts["shmem"] = shmem
            image_min_slots = copy.deepcopy(image_min_slots)
            image_min_slots["mem"] += shmem

            # Sanitize user input: does it have resource config?
            if (resources := creation_config.get("resources")) is not None:
                # Sanitize user input: does it have "known" resource slots only?
                for slot_key, slot_value in resources.items():
                    if slot_value != 0 and slot_key not in known_slot_types:
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
                "uid": kernel["uid"],
                "main_gid": kernel["main_gid"],
                "gids": kernel["supplementary_gids"],
                "image": image_ref.canonical,
                # "image_id": image_row.id,
                "architecture": image_ref.architecture,
                "registry": image_ref.registry,
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
        await self.event_producer.anycast_and_broadcast_event(
            SessionEnqueuedAnycastEvent(session_id, session_creation_id),
            SessionEnqueuedBroadcastEvent(session_id, session_creation_id),
        )
        return session_id

    async def _check_and_pull_in_one_agent(
        self,
        agent_alloc_ctx: AgentAllocationContext,
        kernel_agent_bindings: Sequence[KernelAgentBinding],
        image_configs: Mapping[str, ImageConfig],
    ) -> dict[str, uuid.UUID]:
        """
        Initiates image verification and pulling tasks and returns their mapping.

        This function makes RPC calls to agents to:
        1. Spawn background tasks that verify image existence
        2. Pull missing images if necessary

        Returns:
            dict[str, uuid.UUID]: A dictionary where:
                - keys are image names as strings
                - values are background task IDs
        """
        assert agent_alloc_ctx.agent_id is not None

        agent_client = self._get_agent_client(agent_alloc_ctx.agent_id)
        resp = await agent_client.check_and_pull(image_configs)
        resp = cast(dict[str, str], resp)
        return {img: uuid.UUID(hex=bgtask_id) for img, bgtask_id in resp.items()}

    async def check_and_pull_images(
        self,
        bindings: Iterable[KernelAgentBinding],
    ) -> None:
        if not bindings:
            return
        auto_pull = self.config_provider.config.docker.image.auto_pull.value

        def _keyfunc(binding: KernelAgentBinding) -> AgentId:
            if binding.agent_alloc_ctx.agent_id is None:
                allocated_agent = cast(Optional[AgentId], binding.kernel.agent)
                if allocated_agent is None:
                    log.exception(
                        f"Scheduled kernels should be assigned to a valid agent, skip pulling image (k:{binding.kernel.id})"
                    )
                    return AgentId("")
                binding.agent_alloc_ctx.agent_id = allocated_agent
            return binding.agent_alloc_ctx.agent_id

        async with aiotools.PersistentTaskGroup() as tg:
            for agent_id, group_iterator in itertools.groupby(
                sorted(bindings, key=_keyfunc),
                key=_keyfunc,
            ):
                if not agent_id or agent_id == AgentId(""):
                    continue
                items: list[KernelAgentBinding] = [*group_iterator]
                # Within a group, agent_alloc_ctx are same.
                agent_alloc_ctx = items[0].agent_alloc_ctx
                _img_conf_map: dict[str, ImageConfig] = {}
                for binding in items:
                    img_row = cast(Optional[ImageRow], binding.kernel.image_row)
                    if img_row is not None:
                        img_ref = img_row.image_ref
                        registry_row = cast(ContainerRegistryRow, img_row.registry_row)
                        _img_conf_map[str(img_ref)] = {
                            "architecture": img_row.architecture,
                            "project": img_row.project,
                            "canonical": img_ref.canonical,
                            "is_local": img_row.is_local,
                            "digest": img_row.trimmed_digest,
                            "labels": img_row.labels,
                            "repo_digest": None,
                            "registry": {
                                "name": img_ref.registry,
                                "url": registry_row.url,
                                "username": registry_row.username,
                                "password": registry_row.password,
                            },
                            "auto_pull": AutoPullBehavior(auto_pull),
                        }
                tg.create_task(
                    self._check_and_pull_in_one_agent(agent_alloc_ctx, items, _img_conf_map)
                )

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
                    scaling_group=scheduled_session.scaling_group_name,
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
        async with self.db.connect() as db_conn:
            async with self.db.begin_readonly_session(db_conn) as db_sess:
                resouce_policy_q = sa.select(KeyPairRow.resource_policy).where(
                    KeyPairRow.access_key == scheduled_session.access_key
                )
                query = sa.select(KeyPairResourcePolicyRow).where(
                    KeyPairResourcePolicyRow.name == resouce_policy_q.scalar_subquery()
                )
                result = await db_sess.execute(query)
                resource_policy = result.scalars().first()
                idle_timeout = cast(int, resource_policy.idle_timeout)
                auto_pull = self.config_provider.config.docker.image.auto_pull.value

                # Aggregate image registry information
                image_refs: set[ImageRef] = set()

                for binding in kernel_agent_bindings:
                    image_refs.add(
                        (
                            await ImageRow.resolve(
                                db_sess,
                                [
                                    ImageIdentifier(
                                        binding.kernel.image, binding.kernel.architecture
                                    )
                                ],
                            )
                        ).image_ref
                    )

                _log_msg = ",".join([
                    f"image ref => {ref} ({ref.architecture})" for ref in image_refs
                ])
                log.debug(f"start_session(): {_log_msg}")
                configs = await bulk_get_image_configs(
                    image_refs,
                    AutoPullBehavior(auto_pull),
                    db_session=db_sess,
                )
        img_configs = {item["canonical"]: item for item in configs}

        network_name: Optional[str] = None
        network_config: Mapping[str, Any] = {}
        cluster_ssh_port_mapping: Optional[Dict[str, Tuple[str, int]]] = None
        match scheduled_session.network_type:
            case NetworkType.PERSISTENT:
                async with self.db.begin_readonly_session() as db_sess:
                    network = await NetworkRow.get(db_sess, scheduled_session.network_id)
                    network_name = network.ref_name
                    network_config = {"mode": network.driver, **network.options}
            case NetworkType.VOLATILE:
                if (
                    ClusterMode(scheduled_session.cluster_mode) == ClusterMode.SINGLE_NODE
                    and scheduled_session.cluster_size > 1
                ):
                    network_name = f"bai-singlenode-{scheduled_session.id}"
                    agent_alloc_ctx = kernel_agent_bindings[0].agent_alloc_ctx
                    assert agent_alloc_ctx.agent_id is not None
                    assert scheduled_session.id is not None
                    try:
                        agent_client = self._get_agent_client(
                            agent_alloc_ctx.agent_id,
                            order_key=str(scheduled_session.main_kernel.id),
                        )
                        await agent_client.create_local_network(network_name)
                    except Exception:
                        log.exception(f"Failed to create an agent-local network {network_name}")
                        raise
                    network_config = {
                        "mode": "bridge",
                        "network_name": network_name,
                    }
                elif ClusterMode(scheduled_session.cluster_mode) == ClusterMode.MULTI_NODE:
                    # Create overlay network for multi-node sessions
                    driver = self.config_provider.config.network.inter_container.default_driver
                    if driver is None:
                        raise ValueError("No inter-container network driver is configured.")

                    network_plugin = self.network_plugin_ctx.plugins[driver]
                    try:
                        network_info = await network_plugin.create_network(
                            identifier=scheduled_session.id
                        )
                        network_config = network_info.options
                        network_name = network_info.network_id
                    except Exception:
                        log.exception(
                            f"Failed to create the inter-container network (plugin: {driver})"
                        )
                        raise
            case NetworkType.HOST:
                network_config = {"mode": "host"}
                network_name = "host"
                if scheduled_session.cluster_size > 1:
                    keyfunc = lambda binding: binding.kernel.cluster_role
                    cluster_ssh_port_mapping = {}
                    for cluster_role, group_iterator in itertools.groupby(
                        sorted(kernel_agent_bindings, key=keyfunc),
                        key=keyfunc,
                    ):
                        for index, item in enumerate(group_iterator):
                            assert item.agent_alloc_ctx.agent_id is not None
                            agent_client = self._get_agent_client(
                                item.agent_alloc_ctx.agent_id,
                                order_key=str(scheduled_session.id),
                            )
                            port = await agent_client.assign_port()
                            agent_addr = item.agent_alloc_ctx.agent_addr.replace(
                                "tcp://", ""
                            ).split(":", maxsplit=1)[0]
                            cluster_ssh_port_mapping[item.kernel.cluster_hostname] = (
                                agent_addr,
                                port,
                            )
                            item.allocated_host_ports.add(port)
        log.debug("ssh connection info mapping: {}", cluster_ssh_port_mapping)

        if scheduled_session.network_type == NetworkType.VOLATILE:

            async def _update_network_id(db_sess: AsyncSession) -> None:
                query = (
                    sa.update(SessionRow)
                    .values({
                        "network_id": network_name,
                    })
                    .where(SessionRow.id == scheduled_session.id)
                )
                await db_sess.execute(query)

            async with self.db.connect() as db_conn:
                await execute_with_txn_retry(_update_network_id, self.db.begin_session, db_conn)

        keyfunc = lambda binding: binding.kernel.cluster_role
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
            network_config=network_config,
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
        keyfunc = lambda binding: binding.agent_alloc_ctx.agent_id
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
                        img_configs,
                        cluster_info,
                        idle_timeout,
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

    async def _create_kernels_in_one_agent(
        self,
        agent_alloc_ctx: AgentAllocationContext,
        scheduled_session: SessionRow,
        items: Sequence[KernelAgentBinding],
        image_configs: Mapping[str, ImageConfig],
        cluster_info: ClusterInfo,
        idle_timeout: float | int,
    ) -> None:
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

        try:

            def get_image_conf(kernel: KernelRow) -> ImageConfig:
                return image_configs[kernel.image]

            kernel_image_refs: dict[KernelId, ImageRef] = {}

            raw_configs: list[KernelCreationConfig] = []
            async with self.db.begin_readonly_session() as db_sess:
                for binding in items:
                    kernel_image_refs[binding.kernel.id] = (
                        await ImageRow.resolve(
                            db_sess,
                            [ImageIdentifier(binding.kernel.image, binding.kernel.architecture)],
                        )
                    ).image_ref

                    raw_configs.append({
                        "image": {
                            # TODO: refactor registry and is_local to be specified per kernel.
                            "registry": get_image_conf(binding.kernel)["registry"],
                            "project": get_image_conf(binding.kernel)["project"],
                            "digest": get_image_conf(binding.kernel)["digest"],
                            "repo_digest": get_image_conf(binding.kernel)["repo_digest"],
                            "canonical": get_image_conf(binding.kernel)["canonical"],
                            "architecture": get_image_conf(binding.kernel)["architecture"],
                            "labels": get_image_conf(binding.kernel)["labels"],
                            "is_local": get_image_conf(binding.kernel)["is_local"],
                            "auto_pull": get_image_conf(binding.kernel)["auto_pull"],
                        },
                        "network_id": str(scheduled_session.id),
                        "session_type": scheduled_session.session_type.value,
                        "kernel_id": str(binding.kernel.id),
                        "session_id": str(scheduled_session.id),
                        "owner_user_id": str(scheduled_session.user_uuid),
                        "owner_project_id": None,  # TODO: Implement project-owned sessions
                        "cluster_role": binding.kernel.cluster_role,
                        "cluster_idx": binding.kernel.cluster_idx,
                        "cluster_mode": binding.kernel.cluster_mode,
                        "package_directory": tuple(),
                        "local_rank": binding.kernel.local_rank,
                        "cluster_hostname": binding.kernel.cluster_hostname,
                        "uid": binding.kernel.uid,
                        "main_gid": binding.kernel.main_gid,
                        "supplementary_gids": binding.kernel.gids or [],
                        "idle_timeout": int(idle_timeout),
                        "mounts": [item.to_json() for item in scheduled_session.vfolder_mounts],
                        "environ": {
                            # inherit per-session environment variables
                            **scheduled_session.environ,
                            # set per-kernel environment variables
                            "BACKENDAI_KERNEL_ID": str(binding.kernel.id),
                            "BACKENDAI_KERNEL_IMAGE": get_image_conf(binding.kernel)["canonical"],
                            "BACKENDAI_CLUSTER_ROLE": binding.kernel.cluster_role,
                            "BACKENDAI_CLUSTER_IDX": str(binding.kernel.cluster_idx),
                            "BACKENDAI_CLUSTER_LOCAL_RANK": str(binding.kernel.local_rank),
                            "BACKENDAI_CLUSTER_HOST": str(binding.kernel.cluster_hostname),
                            "BACKENDAI_SERVICE_PORTS": str(
                                get_image_conf(binding.kernel)["labels"].get(
                                    "ai.backend.service-ports"
                                )
                            ),
                        },
                        "resource_slots": binding.kernel.requested_slots.to_json(),
                        "resource_opts": binding.kernel.resource_opts,
                        "bootstrap_script": binding.kernel.bootstrap_script,
                        "startup_command": binding.kernel.startup_command,
                        "internal_data": scheduled_session.main_kernel.internal_data,
                        "auto_pull": get_image_conf(binding.kernel)["auto_pull"],
                        "preopen_ports": scheduled_session.main_kernel.preopen_ports,
                        "allocated_host_ports": list(binding.allocated_host_ports),
                        "agent_addr": binding.agent_alloc_ctx.agent_addr,
                        "scaling_group": binding.agent_alloc_ctx.scaling_group,
                        "endpoint_id": None,
                    })

                raw_kernel_ids = [str(binding.kernel.id) for binding in items]

            # Issue a batched RPC call to create kernels on this agent
            # created_infos = await agent_client.create_kernels(
            agent_client = self._get_agent_client(
                agent_alloc_ctx.agent_id,
                order_key=str(scheduled_session.id),
            )
            await agent_client.create_kernels(
                str(scheduled_session.id),
                raw_kernel_ids,
                raw_configs,
                cluster_info,
                kernel_image_refs,
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
        known_slot_types = await self.config_provider.legacy_etcd_config_loader.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                query = sa.select(KernelRow.occupied_slots).where(
                    (KernelRow.user_uuid == user_id)
                    & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                    & (KernelRow.session_type.not_in(PRIVATE_SESSION_TYPES))
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
        known_slot_types = await self.config_provider.legacy_etcd_config_loader.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                query = (
                    sa.select(KernelRow.occupied_slots)
                    .select_from(KernelRow)
                    .where(
                        (KernelRow.access_key == access_key)
                        & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                        & (KernelRow.session_type.not_in(PRIVATE_SESSION_TYPES)),
                    )
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
        known_slot_types = await self.config_provider.legacy_etcd_config_loader.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                query = (
                    sa.select(KernelRow.occupied_slots)
                    .select_from(KernelRow)
                    .where(
                        (KernelRow.domain_name == domain_name)
                        & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                        & (KernelRow.session_type.not_in(PRIVATE_SESSION_TYPES)),
                    )
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
        known_slot_types = await self.config_provider.legacy_etcd_config_loader.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                query = (
                    sa.select(KernelRow.occupied_slots)
                    .select_from(KernelRow)
                    .where(
                        (KernelRow.group_id == group_id)
                        & (KernelRow.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES))
                        & (KernelRow.session_type.not_in(PRIVATE_SESSION_TYPES)),
                    )
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
        agent_client = self._get_agent_client(agent["id"])
        await agent_client.update_scaling_group(scaling_group)

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
                        load_only(
                            SessionRow.id,
                            SessionRow.access_key,
                            SessionRow.status,
                            SessionRow.session_type,
                        ),
                        selectinload(SessionRow.kernels).options(
                            load_only(KernelRow.agent, KernelRow.occupied_slots)
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
                        if session_row.status in USER_RESOURCE_OCCUPYING_SESSION_STATUSES:
                            access_key = cast(AccessKey, session_row.access_key)
                            if access_key not in access_key_to_concurrency_used:
                                access_key_to_concurrency_used[access_key] = ConcurrencyUsed(
                                    access_key
                                )
                            if session_row.session_type in PRIVATE_SESSION_TYPES:
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
        await self._update_concurrency(access_key_to_concurrency_used, do_fullscan)

    async def _update_concurrency(
        self,
        access_key_to_concurrency_used: Mapping[AccessKey, ConcurrencyUsed],
        do_fullscan: bool,
    ) -> None:
        """Update concurrency values in valkey based on the current state."""
        # Do full scan if the entire system does not have ANY sessions/sftp-sessions
        # to set all concurrency_used to 0
        _do_fullscan = do_fullscan or not access_key_to_concurrency_used
        if _do_fullscan:
            # Convert ConcurrencyUsed objects to simple access_key -> count mapping
            # For fullscan, we need both compute and system concurrency counts
            access_key_to_count = {
                str(ak): len(concurrency.compute_session_ids)
                for ak, concurrency in access_key_to_concurrency_used.items()
            }
            await self.valkey_stat.update_concurrency_by_fullscan(access_key_to_count)
        else:
            # Update keypair resource usage for keypairs with running containers.
            # Prepare separate maps for compute and system concurrency
            compute_concurrency_map = {}
            system_concurrency_map = {}
            for concurrency in access_key_to_concurrency_used.values():
                compute_concurrency_map[str(concurrency.access_key)] = len(
                    concurrency.compute_session_ids
                )
                system_concurrency_map[str(concurrency.access_key)] = len(
                    concurrency.system_session_ids
                )

            # Update compute concurrency
            if compute_concurrency_map:
                await self.valkey_stat.update_compute_concurrency_by_map(compute_concurrency_map)

            # Update system concurrency
            if system_concurrency_map:
                await self.valkey_stat.update_system_concurrency_by_map(system_concurrency_map)

    async def destroy_session_lowlevel(
        self,
        session_id: SessionId,
        kernels: Sequence[
            Mapping[str, Any]
        ],  # should have (id, agent, agent_addr, container_id) columns
        reason: KernelLifecycleEventReason = KernelLifecycleEventReason.FAILED_TO_START,
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
            for kernel in destroyed_kernels:

                async def destory_kernel() -> None:
                    agent_client = self._get_agent_client(
                        destroyed_kernels[0]["agent"], order_key=str(session_id)
                    )
                    await agent_client.destroy_kernel(
                        str(kernel["id"]),
                        str(session_id),
                        reason,
                        suppress_events=True,
                    )

                # internally it enqueues a "destroy" lifecycle event.
                rpc_coros.append(destory_kernel())
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
        CREATING/TERMINATING/ERROR and PULLING sessions.

        :param forced: If True, destroy CREATING/TERMINATING/ERROR session.
        :param reason: Reason to destroy a session if client wants to specify it manually.
        :param user_role: Role of the user who requested the session destruction.
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

        async def _force_destroy_for_superadmin(
            target_status: Literal[SessionStatus.CANCELLED, SessionStatus.TERMINATED],
        ) -> None:
            current_time = datetime.now(tzutc())
            destroy_reason = str(KernelLifecycleEventReason.FORCE_TERMINATED)

            async def _destroy(db_session: AsyncSession) -> SessionRow:
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

            async with self.db.connect() as db_conn:
                await execute_with_txn_retry(_destroy, self.db.begin_session, db_conn)
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
                    load_only(
                        SessionRow.creation_id,
                        SessionRow.status,
                        SessionRow.access_key,
                        SessionRow.session_type,
                    ),
                    selectinload(SessionRow.kernels).options(
                        noload("*"),
                        load_only(
                            KernelRow.id,
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

            target_session = cast(SessionRow, target_session)

            async def _decrease_concurrency_used(access_key: AccessKey, is_private: bool) -> None:
                await self.valkey_stat.decrement_keypair_concurrency(
                    access_key=str(access_key),
                    is_private=is_private,
                )

            match target_session.status:
                case SessionStatus.PENDING:
                    await SessionRow.set_session_status(
                        self.db, session_id, SessionStatus.CANCELLED
                    )
                case (
                    SessionStatus.SCHEDULED
                    | SessionStatus.PREPARING
                    | SessionStatus.PULLING
                    | SessionStatus.PREPARED
                    | SessionStatus.CREATING
                    | SessionStatus.TERMINATING
                    | SessionStatus.ERROR
                ):
                    if not forced:
                        raise GenericForbidden(
                            "Cannot destroy sessions in scheduled/preparing/pulling/prepared/creating/terminating/error"
                            " status",
                        )
                    log.warning(
                        "force-terminating session (s:{}, status:{})",
                        session_id,
                        target_session.status,
                    )
                    await _decrease_concurrency_used(
                        target_session.access_key, target_session.is_private
                    )
                    if user_role == UserRole.SUPERADMIN:
                        # Exceptionally let superadmins set the session status to 'TERMINATED' and finish the function.
                        # TODO: refactor Session/Kernel status management and remove this.
                        await _force_destroy_for_superadmin(SessionStatus.TERMINATED)
                        return {}
                    else:
                        await SessionRow.set_session_status(
                            self.db, session_id, SessionStatus.TERMINATING
                        )
                        await self.event_producer.anycast_and_broadcast_event(
                            SessionTerminatingAnycastEvent(session_id, reason),
                            SessionTerminatingBroadcastEvent(session_id, reason),
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
                    await _decrease_concurrency_used(
                        target_session.access_key, target_session.is_private
                    )
                    await SessionRow.set_session_status(
                        self.db, session_id, SessionStatus.TERMINATING
                    )
                    await self.event_producer.anycast_and_broadcast_event(
                        SessionTerminatingAnycastEvent(session_id, reason),
                        SessionTerminatingBroadcastEvent(session_id, reason),
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
                        case KernelStatus.PENDING | KernelStatus.PULLING:
                            await KernelRow.set_kernel_status(
                                self.db,
                                kernel.id,
                                KernelStatus.CANCELLED,
                                reason=reason,
                                status_changed_at=now,
                            )
                            await self.event_producer.anycast_event(
                                KernelCancelledAnycastEvent(kernel.id, session_id, reason),
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
                                await self.event_producer.anycast_and_broadcast_event(
                                    SessionCancelledAnycastEvent(
                                        session_id,
                                        target_session.creation_id,
                                        reason,
                                    ),
                                    SessionCancelledBroadcastEvent(
                                        session_id,
                                        target_session.creation_id,
                                        reason,
                                    ),
                                )
                        case (
                            KernelStatus.SCHEDULED
                            | KernelStatus.PREPARING
                            | KernelStatus.PREPARED
                            | KernelStatus.CREATING
                            | KernelStatus.TERMINATING
                            | KernelStatus.ERROR
                        ):
                            if not forced:
                                raise GenericForbidden(
                                    "Cannot destroy kernels in"
                                    " scheduled/prepared/preparing/terminating/error status",
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
                                kern_stat = await self.valkey_stat.get_kernel_statistics(
                                    str(kernel.id)
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
                                        values["last_stat"] = kern_stat
                                    await db_sess.execute(
                                        sa.update(KernelRow)
                                        .values(**values)
                                        .where(KernelRow.id == kernel.id),
                                    )

                            await execute_with_retry(_update)
                            await self.event_producer.anycast_event(
                                KernelTerminatedAnycastEvent(kernel.id, target_session.id, reason),
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

                            await execute_with_retry(_update)
                            await self.event_producer.anycast_event(
                                KernelTerminatingAnycastEvent(kernel.id, target_session.id, reason),
                            )

                    if kernel.agent_addr is None:
                        async with self.db.connect() as db_conn:
                            await self.mark_kernel_terminated(
                                db_conn, kernel.id, target_session.id, "missing-agent-allocation"
                            )
                        if kernel.cluster_role == DEFAULT_ROLE:
                            main_stat = {"status": "terminated"}
                    else:
                        destroyed_kernels.append(kernel)

                async def _destroy_kernels_in_agent(
                    session: SessionRow, destroyed_kernels: List[KernelRow]
                ) -> None:
                    nonlocal main_stat
                    rpc_coros = []
                    for kernel in destroyed_kernels:
                        # internally it enqueues a "destroy" lifecycle event.
                        if kernel.status != KernelStatus.SCHEDULED:

                            async def destroy_kernel() -> None:
                                agent_client = self._get_agent_client(
                                    destroyed_kernels[0].agent,
                                    order_key=str(session.id),
                                )
                                await agent_client.destroy_kernel(
                                    str(kernel.id),
                                    str(session.id),
                                    reason,
                                    suppress_events=True,
                                )

                            rpc_coros.append(destroy_kernel())
                    try:
                        await asyncio.gather(*rpc_coros)
                    except Exception:
                        log.exception(
                            "destroy_kernels_in_agent(a:{}, s:{}): unexpected error",
                            destroyed_kernels[0].agent,
                            session.id,
                        )
                    for kernel in destroyed_kernels:
                        last_stat: Optional[dict[str, Any]]
                        last_stat = None
                        try:
                            last_stat = await self.valkey_stat.get_kernel_statistics(
                                str(kernel.id),
                            )
                            if last_stat is not None:
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
                await self.event_producer.anycast_event(
                    KernelTerminatedAnycastEvent(kernel.id, target_session.id, reason),
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
        async def _fetch_session() -> tuple[SessionRow, str | None]:
            async with self.db.begin_readonly_session() as db_sess:
                sess = await SessionRow.get_session_by_id(
                    db_sess,
                    session_id,
                    eager_loading_op=(
                        noload("*"),
                        selectinload(SessionRow.kernels).options(
                            noload("*"),
                            selectinload(KernelRow.agent_row).noload("*"),
                        ),
                    ),
                )
                network_ref_name = await sess.get_network_ref(db_sess)
                return sess, network_ref_name

        try:
            session, network_ref_name = await execute_with_retry(_fetch_session)
        except SessionNotFound:
            return

        # Get the main container's agent info

        # TODO: Separate VOLATILE network cleanup method
        if session.network_type == NetworkType.VOLATILE:
            if ClusterMode(session.cluster_mode) == ClusterMode.SINGLE_NODE:
                if network_ref_name is not None:
                    try:
                        agent_client = self._get_agent_client(
                            session.main_kernel.agent,
                            order_key=str(session.main_kernel.session_id),
                        )
                        await agent_client.destroy_local_network(network_ref_name)
                    except Exception:
                        log.exception(
                            f"Failed to destroy the agent-local network {network_ref_name}"
                        )
            elif ClusterMode(session.cluster_mode) == ClusterMode.MULTI_NODE:
                if network_ref_name is None:
                    raise ValueError("network_id should not be None!")
                if self.config_provider.config.network.inter_container.default_driver is None:
                    raise ValueError("No inter-container network driver is configured.")

                network_plugin = self.network_plugin_ctx.plugins[
                    self.config_provider.config.network.inter_container.default_driver
                ]
                try:
                    await network_plugin.destroy_network(network_ref_name)
                except Exception:
                    log.exception(f"Failed to destroy the overlay network {network_ref_name}")
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
                updated_config: Dict[str, Any] = {
                    # TODO: support rescaling of sub-containers
                }
                async with self.db.begin_session() as db_sess:
                    image_row = await ImageRow.resolve(
                        db_sess, [ImageIdentifier(kernel.image, kernel.architecture)]
                    )

                agent_client = self._get_agent_client(kernel.agent)
                kernel_info = await agent_client.restart_kernel(
                    str(kernel.session_id),
                    str(kernel.id),
                    image_row.image_ref,
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
        await self.event_producer.anycast_and_broadcast_event(
            SessionStartedAnycastEvent(session.id, session.creation_id),
            SessionStartedBroadcastEvent(session.id, session.creation_id),
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
        flush_timeout: Optional[float] = None,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            # The agent aggregates at most 2 seconds of outputs
            # if the kernel runs for a long time.
            major_api_version = api_version[0]
            if major_api_version == 4:  # manager-agent protocol is same.
                major_api_version = 3
            agent_client = self._get_agent_client(
                session.main_kernel.agent,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
            )
            return await agent_client.execute(
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
            agent_client = self._get_agent_client(
                session.main_kernel.agent,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
            )
            return await agent_client.trigger_batch_execution(
                str(session.id),
                str(session.main_kernel.id),
                session.main_kernel.startup_command or "",
                session.batch_timeout,
            )

    async def interrupt_session(
        self,
        session: SessionRow,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            agent_client = self._get_agent_client(
                session.main_kernel.agent,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
            )
            return await agent_client.interrupt_kernel(str(session.main_kernel.id))

    async def get_completions(
        self,
        session: SessionRow,
        text: str,
        opts: Mapping[str, Any],
    ) -> CodeCompletionResp:
        async with handle_session_exception(self.db, "execute", session.id):
            # NOTE: Callosum serialize all inputs to dict and upack all array inputs to tuples
            agent_client = self._get_agent_client(
                session.main_kernel.agent,
                invoke_timeout=10,
                order_key=session.main_kernel.id,
            )
            result = await agent_client.get_completions(str(session.main_kernel.id), text, opts)
            return CodeCompletionResp.from_dict(result)

    async def start_service(
        self,
        session: SessionRow,
        service: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "execute", session.id):
            agent_client = self._get_agent_client(
                session.main_kernel.agent,
                order_key=session.main_kernel.id,
            )
            return await agent_client.start_service(str(session.main_kernel.id), service, opts)

    async def shutdown_service(
        self,
        session: SessionRow,
        service: str,
    ) -> None:
        async with handle_session_exception(self.db, "shutdown_service", session.id):
            agent_client = self._get_agent_client(
                session.main_kernel.agent,
                order_key=session.main_kernel.id,
            )
            return await agent_client.shutdown_service(str(session.main_kernel.id), service)

    async def upload_file(
        self,
        session: SessionRow,
        filename: str,
        payload: bytes,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "upload_file", session.id):
            agent_client = self._get_agent_client(
                session.main_kernel.agent,
                order_key=session.main_kernel.id,
            )
            return await agent_client.upload_file(str(session.main_kernel.id), filename, payload)

    async def download_file(
        self,
        session: SessionRow,
        filepath: str,
    ) -> bytes:
        kernel = session.main_kernel
        async with handle_session_exception(self.db, "download_file", kernel.session_id):
            agent_client = self._get_agent_client(
                session.main_kernel.agent,
                order_key=kernel.id,
            )
            return await agent_client.download_file(str(kernel.id), filepath)

    async def download_single(
        self,
        session: SessionRow,
        access_key: AccessKey,
        filepath: str,
    ) -> bytes:
        kernel = session.main_kernel
        async with handle_session_exception(self.db, "download_single", kernel.session_id):
            agent_client = self._get_agent_client(kernel.agent, order_key=kernel.id)
            return await agent_client.download_single(str(kernel.id), filepath)

    async def list_files(
        self,
        session: SessionRow,
        path: str,
    ) -> Mapping[str, Any]:
        async with handle_session_exception(self.db, "list_files", session.id):
            agent_client = self._get_agent_client(
                session.main_kernel.agent,
                invoke_timeout=30,
                order_key=session.main_kernel.id,
            )
            return await agent_client.list_files(str(session.main_kernel.id), path)

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
            if kernel.agent is None:
                raise InstanceNotFound(
                    "Kernel has not been assigned to an agent.", extra_data={"kernel_id": kernel_id}
                )
            agent_client = self._get_agent_client(
                agent_id=kernel.agent,
                invoke_timeout=30,
                order_key=kernel.id,
            )
            reply = await agent_client.get_logs(str(kernel.id))
            return reply["logs"]

    async def increment_session_usage(
        self,
        session: SessionRow,
    ) -> None:
        # noop for performance reasons
        pass

    async def handle_agent_images_remove(
        self, agent_id: AgentId, image_canonicals: list[str]
    ) -> None:
        await self.valkey_image.remove_agent_from_images(agent_id, image_canonicals)

    async def mark_agent_terminated(self, agent_id: AgentId, status: AgentStatus) -> None:
        await self.valkey_live.remove_agent_last_seen(agent_id)

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

        await self.valkey_image.remove_agent_from_all_images(agent_id)
        await execute_with_retry(_update)

    async def sync_kernel_stats(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> None:
        per_kernel_updates = {}
        log.debug("sync_kernel_stats(k:{!r})", kernel_ids)
        for kernel_id in kernel_ids:
            raw_kernel_id = str(kernel_id)
            kern_stat = await self.valkey_stat.get_kernel_statistics(raw_kernel_id)
            if kern_stat is None:
                log.warning("sync_kernel_stats(k:{}): no statistics updates", kernel_id)
                continue
            else:
                per_kernel_updates[kernel_id] = kern_stat

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
            agent_client = self._get_agent_client(agent_id)
            return await agent_client.sync_kernel_registry([
                (str(kernel.id), str(kernel.session_id)) for kernel in grouped_kernels
            ])

    async def mark_image_pull_started(
        self,
        agent_id: AgentId,
        image_canonical: str,
        image_ref: Optional[ImageRef] = None,
        *,
        db_conn: SAConnection,
    ) -> None:
        async def _transit(db_session: AsyncSession) -> set[SessionId]:
            canonical = image_ref.canonical if image_ref is not None else image_canonical
            session_ids: set[SessionId] = set()
            _stmt = (
                sa.select(KernelRow)
                .where(
                    (KernelRow.image == canonical)
                    & (KernelRow.agent == agent_id)
                    & (KernelRow.status.in_((KernelStatus.SCHEDULED, KernelStatus.PREPARING)))
                )
                # Ensures transition
                .with_for_update()
            )
            for row in await db_session.scalars(_stmt):
                kernel_row = cast(KernelRow, row)
                is_pulling = kernel_row.transit_status(KernelStatus.PULLING)
                if is_pulling:
                    session_ids.add(kernel_row.session_id)
            return session_ids

        session_ids = await execute_with_txn_retry(_transit, self.db.begin_session, db_conn)
        if session_ids:
            await self.session_lifecycle_mgr.register_status_updatable_session(session_ids)

    async def mark_image_pull_finished(
        self,
        agent_id: AgentId,
        image_canonical: str,
        image_ref: Optional[ImageRef] = None,
        *,
        db_conn: SAConnection,
    ) -> None:
        async def _transit(db_session: AsyncSession) -> set[SessionId]:
            canonical = image_ref.canonical if image_ref is not None else image_canonical
            session_ids: set[SessionId] = set()
            _stmt = (
                sa.select(KernelRow)
                .where(
                    (KernelRow.image == canonical)
                    & (KernelRow.agent == agent_id)
                    & (
                        KernelRow.status.in_((
                            KernelStatus.SCHEDULED,
                            KernelStatus.PREPARING,
                            KernelStatus.PULLING,
                        ))
                    )
                )
                # Ensures transition
                .with_for_update()
            )
            for row in await db_session.scalars(_stmt):
                kernel_row = cast(KernelRow, row)
                is_ready = kernel_row.transit_status(KernelStatus.PREPARED)
                if is_ready:
                    session_ids.add(kernel_row.session_id)
            return session_ids

        session_ids = await execute_with_txn_retry(_transit, self.db.begin_session, db_conn)
        if session_ids:
            await self.session_lifecycle_mgr.register_status_updatable_session(session_ids)

    async def handle_image_pull_failed(
        self,
        agent_id: AgentId,
        image_canonical: str,
        msg: str,
        image_ref: Optional[ImageRef] = None,
        *,
        db_conn: SAConnection,
    ) -> None:
        async def _transit(db_session: AsyncSession) -> set[SessionId]:
            canonical = image_ref.canonical if image_ref is not None else image_canonical
            session_ids: set[SessionId] = set()
            _stmt = (
                sa.select(KernelRow)
                .where(
                    (KernelRow.image == canonical)
                    & (KernelRow.agent == agent_id)
                    & (KernelRow.status.in_((KernelStatus.SCHEDULED, KernelStatus.PULLING)))
                )
                # Ensures transition
                .with_for_update()
            )
            for row in await db_session.scalars(_stmt):
                kernel_row = cast(KernelRow, row)
                is_transited = kernel_row.transit_status(
                    KernelStatus.CANCELLED,
                    status_info="image-pull-failed",
                    status_data={"error": {"src": "other", "repr": msg}},
                )
                if is_transited:
                    session_ids.add(kernel_row.session_id)

            return session_ids

        session_ids = await execute_with_txn_retry(_transit, self.db.begin_session, db_conn)
        if session_ids:
            await self.session_lifecycle_mgr.register_status_updatable_session(session_ids)

    async def mark_kernel_creating(
        self,
        db_conn: SAConnection,
        kernel_id: KernelId,
        session_id: SessionId,
        reason: str,
    ) -> None:
        now = datetime.now(tzutc())

        async def _set_status(db_session: AsyncSession) -> None:
            kernel_row = await KernelRow.get_kernel_to_update_status(db_session, kernel_id)
            kernel_row.transit_status(
                KernelStatus.CREATING, reason, status_data={}, status_changed_at=now
            )

        await execute_with_txn_retry(_set_status, self.db.begin_session, db_conn)
        await self.session_lifecycle_mgr.register_status_updatable_session([session_id])

    async def mark_kernel_pulling(
        self,
        db_conn: SAConnection,
        kernel_id: KernelId,
        session_id: SessionId,
        reason: str,
    ) -> None:
        now = datetime.now(tzutc())

        async def _transit_status(db_session: AsyncSession) -> bool:
            kernel_row = await KernelRow.get_kernel_to_update_status(db_session, kernel_id)
            is_pulling = kernel_row.transit_status(
                KernelStatus.PULLING, reason, status_changed_at=now
            )
            if is_pulling:
                await db_session.commit()
            return is_pulling

        transited = await execute_with_txn_retry(_transit_status, self.db.begin_session, db_conn)
        if transited:
            await self.session_lifecycle_mgr.register_status_updatable_session([session_id])

    async def mark_kernel_running(
        self,
        db_conn: SAConnection,
        kernel_id: KernelId,
        session_id: SessionId,
        reason: str,
        created_info: Mapping[str, Any],
    ) -> None:
        now = datetime.now(tzutc())
        agent_host = URL(created_info["agent_addr"]).host
        actual_allocs = self.convert_resource_spec_to_resource_slot(
            created_info["resource_spec"]["allocations"]
        )

        async def _get_and_transit(db_session: AsyncSession) -> bool:
            kernel_row = await KernelRow.get_kernel_to_update_status(db_session, kernel_id)
            is_running = kernel_row.transit_status(
                KernelStatus.RUNNING,
                reason,
                status_changed_at=now,
            )
            if is_running:
                kernel_row.occupied_slots = actual_allocs
                kernel_row.container_id = created_info["container_id"]
                kernel_row.attached_devices = created_info.get("attached_devices", {})
                kernel_row.kernel_host = created_info.get("kernel_host", agent_host)
                kernel_row.repl_in_port = created_info["repl_in_port"]
                kernel_row.repl_out_port = created_info["repl_out_port"]
                kernel_row.service_ports = created_info.get("service_ports", [])
                await db_session.commit()
            return is_running

        transited = await execute_with_txn_retry(_get_and_transit, self.db.begin_session, db_conn)

        if transited:
            self._kernel_actual_allocated_resources[kernel_id] = actual_allocs
            await self.session_lifecycle_mgr.register_status_updatable_session([session_id])

    async def mark_kernel_terminated(
        self,
        db_conn: SAConnection,
        kernel_id: KernelId,
        session_id: SessionId,
        reason: str,
        exit_code: Optional[int] = None,
    ) -> None:
        """
        Mark the kernel (individual worker) terminated and release
        the resource slots occupied by it.
        """
        last_stat = await self.valkey_stat.get_kernel_statistics(str(kernel_id))
        now = datetime.now(tzutc())

        async def _get_and_transit(
            db_session: AsyncSession,
        ) -> KernelRow | None:
            kernel_row = await KernelRow.get_kernel_to_update_status(db_session, kernel_id)
            is_terminated = kernel_row.transit_status(
                KernelStatus.TERMINATED,
                reason,
                status_data=sql_json_merge(
                    KernelRow.status_data,
                    ("kernel",),
                    {"exit_code": exit_code},
                ),
                status_changed_at=now,
            )
            if not is_terminated:
                return None
            if last_stat is not None:
                kernel_row.last_stat = last_stat
            return kernel_row

        result = await execute_with_txn_retry(_get_and_transit, self.db.begin_session, db_conn)

        if result is None:
            return
        await self.session_lifecycle_mgr.register_status_updatable_session([session_id])

    async def mark_kernel_heartbeat(self, kernel_id: KernelId) -> None:
        last_seen = datetime.now(timezone.utc)
        async with self.db.begin_session() as db_session:
            kernel_row = await KernelRow.get_kernel_to_update_status(db_session, kernel_id)
            kernel_row.last_seen = last_seen

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
        kernel_ids_str = [str(kernel_id) for kernel_id in kernel_ids]
        commit_statuses = await self.valkey_stat.get_kernel_commit_statuses(kernel_ids_str)

        return {
            kernel_id: str(result, "utf-8") if result is not None else CommitStatus.READY.value
            for kernel_id, result in zip(kernel_ids, commit_statuses)
        }

    async def commit_session(
        self,
        session: SessionRow,
        new_image_ref: ImageRef,
        *,
        extra_labels: dict[str | LabelName, str] = {},
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
            agent_client = self._get_agent_client(kernel.agent, order_key=kernel.id)
            resp = await agent_client.commit(
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
        agent_client = self._get_agent_client(agent)
        return await agent_client.push_image(
            image_ref,
            {**registry, "url": str(registry["url"])},
        )

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
        async with handle_session_exception(self.db, "commit_session_to_file", session.id):
            agent_client = self._get_agent_client(kernel.agent, order_key=kernel.id)
            resp = await agent_client.commit(
                str(kernel.id),
                email,
                filename=filename,
                extra_labels=extra_labels,
                canonical=ImageRef.parse_image_str(kernel.image, registry).canonical,
            )
        return resp

    async def get_agent_local_config(
        self,
        agent_id: AgentId,
        agent_addr: str,
    ) -> Mapping[str, str]:
        agent_client = self._get_agent_client(agent_id)
        return await agent_client.get_local_config()

    async def purge_images(self, agent_id: AgentId, request: PurgeImagesReq) -> PurgeImagesResp:
        agent_client = self._get_agent_client(agent_id)
        result = await agent_client.purge_images(request.images, request.force, request.noprune)

        return PurgeImagesResp(
            responses=[
                PurgeImageResp(
                    image=resp["image"],
                    error=resp.get("error"),
                )
                for resp in result["responses"]
            ],
        )

    async def get_abusing_report(
        self,
        kernel_id: KernelId,
    ) -> Optional[AbuseReport]:
        kern_id = str(kernel_id)
        result = await self.valkey_stat.get_abuse_report(kern_id)
        if result is None:
            return None
        return {
            "kernel": kern_id,
            "abuse_report": result,
        }

    async def get_health_check_info(
        self, endpoint: EndpointData, model: VFolderRow
    ) -> ModelHealthCheck | None:
        _info: ModelHealthCheck | None = None

        if _path := MODEL_SERVICE_RUNTIME_PROFILES[endpoint.runtime_variant].health_check_endpoint:
            _info = ModelHealthCheck(path=_path)
        elif endpoint.runtime_variant == RuntimeVariant.CUSTOM:
            model_definition_path = await ModelServiceHelper.validate_model_definition_file_exists(
                self.storage_manager,
                model.host,
                model.vfid,
                endpoint.model_definition_path,
            )
            model_definition = await ModelServiceHelper.validate_model_definition(
                self.storage_manager,
                model.host,
                model.vfid,
                model_definition_path,
            )

            for model_info in model_definition["models"]:
                if health_check_info := model_info.get("service", {}).get("health_check"):
                    _info = ModelHealthCheck(
                        path=health_check_info["path"],
                        interval=health_check_info["interval"],
                        max_retries=health_check_info["max_retries"],
                        max_wait_time=health_check_info["max_wait_time"],
                        expected_status_code=health_check_info["expected_status_code"],
                    )
                    break
        return _info

    async def create_appproxy_endpoint(
        self,
        db_sess: AsyncSession,
        endpoint: EndpointData,
    ) -> str:
        query = (
            sa.select([scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token])
            .select_from(scaling_groups)
            .where((scaling_groups.c.name == endpoint.resource_group))
        )

        result = await db_sess.execute(query)
        sgroup = result.first()
        wsproxy_addr = sgroup["wsproxy_addr"]
        wsproxy_api_token = sgroup["wsproxy_api_token"]
        wsproxy_client = self._load_app_proxy_client(wsproxy_addr, wsproxy_api_token)

        model = await VFolderRow.get(db_sess, endpoint.model)

        health_check_config = await self.get_health_check_info(endpoint, model)

        request_body = CreateEndpointRequestBody(
            version="v2",
            service_name=endpoint.name,
            tags=TagsModel(
                session=SessionTagsModel(
                    user_uuid=str(endpoint.session_owner_id),
                    group_id=str(endpoint.project),
                    domain_name=endpoint.domain,
                ),
                endpoint=EndpointTagsModel(
                    id=str(endpoint.id),
                    runtime_variant=endpoint.runtime_variant.value,
                    existing_url=str(endpoint.url) if endpoint.url else None,
                ),
            ),
            apps={},
            open_to_public=endpoint.open_to_public,
            health_check=health_check_config,
        )
        endpoint_json = await wsproxy_client.create_endpoint(endpoint.id, request_body)
        return endpoint_json["endpoint"]

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

        wsproxy_client = self._load_app_proxy_client(wsproxy_addr, wsproxy_api_token)
        await wsproxy_client.delete_endpoint(endpoint.id)

    async def notify_endpoint_route_update_to_appproxy(self, endpoint_id: uuid.UUID) -> None:
        async with self.db.begin_readonly_session() as db_sess:
            endpoint = await EndpointRow.get(
                db_sess,
                endpoint_id,
                load_created_user=True,
                load_session_owner=True,
                load_image=True,
                load_routes=True,
            )
            connection_info = await endpoint.generate_route_info(db_sess)
            model = await VFolderRow.get(db_sess, endpoint.model)
            endpoint_data = endpoint.to_data()

        health_check_config = await self.get_health_check_info(endpoint_data, model)
        await self.valkey_live.update_appproxy_redis_info(
            endpoint.id,
            connection_info,
            health_check_config,
        )

        await self.event_producer.anycast_event(EndpointRouteListUpdatedEvent(endpoint.id))

    async def purge_containers(
        self,
        agent_id: AgentId,
        container_kernel_ids: Iterable[ContainerKernelId],
    ) -> None:
        serialized = [entry.serialize() for entry in container_kernel_ids]
        if not serialized:
            return
        agent_client = self._get_agent_client(agent_id)
        await agent_client.purge_containers(serialized)

    async def drop_kernel_registry(
        self,
        agent_id: AgentId,
        kernel_ids: Iterable[KernelId],
    ) -> None:
        kernel_id_list = list(kernel_ids)  # Parse the iterable to a list for serialization
        if not kernel_id_list:
            return
        agent_client = self._get_agent_client(agent_id)
        await agent_client.drop_kernel_registry(kernel_id_list)


async def handle_image_pull_started(
    context: AgentRegistry,
    agent_id: AgentId,
    ev: ImagePullStartedEvent,
) -> None:
    dt = datetime.fromtimestamp(ev.timestamp)
    log.debug("handle_image_pull_started: ag:{} img:{}, start_dt:{}", ev.agent_id, ev.image, dt)
    async with context.db.connect() as db_conn:
        await context.mark_image_pull_started(ev.agent_id, ev.image, ev.image_ref, db_conn=db_conn)


async def handle_image_pull_finished(
    context: AgentRegistry, agent_id: AgentId, ev: ImagePullFinishedEvent
) -> None:
    dt = datetime.fromtimestamp(ev.timestamp)
    log.debug("handle_image_pull_finished: ag:{} img:{}, end_dt:{}", ev.agent_id, ev.image, dt)
    async with context.db.connect() as db_conn:
        await context.mark_image_pull_finished(ev.agent_id, ev.image, ev.image_ref, db_conn=db_conn)


async def handle_image_pull_failed(
    context: AgentRegistry,
    agent_id: AgentId,
    ev: ImagePullFailedEvent,
) -> None:
    log.warning("handle_image_pull_failed: ag:{} img:{}, msg:{}", ev.agent_id, ev.image, ev.msg)
    async with context.db.connect() as db_conn:
        await context.handle_image_pull_failed(
            ev.agent_id, ev.image, ev.msg, ev.image_ref, db_conn=db_conn
        )


async def handle_kernel_creation_lifecycle(
    context: AgentRegistry,
    source: AgentId,
    event: KernelPreparingAnycastEvent
    | KernelPullingAnycastEvent
    | KernelCreatingAnycastEvent
    | KernelStartedAnycastEvent
    | KernelCancelledAnycastEvent,
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
        event.event_name(),
        event.kernel_id,
    )
    match event:
        case KernelPreparingAnycastEvent():
            # State transition is done by the DoPrepareEvent handler inside the scheduler-distpacher object.
            pass
        case KernelPullingAnycastEvent(kernel_id, session_id, reason=reason):
            async with context.db.connect() as db_conn:
                await context.mark_kernel_pulling(db_conn, kernel_id, session_id, reason)
        case KernelCreatingAnycastEvent(kernel_id, session_id, reason=reason):
            async with context.db.connect() as db_conn:
                await context.mark_kernel_creating(db_conn, kernel_id, session_id, reason)
        case KernelStartedAnycastEvent(
            kernel_id, session_id, reason=reason, creation_info=creation_info
        ):
            async with context.db.connect() as db_conn:
                await context.mark_kernel_running(
                    db_conn, kernel_id, session_id, reason, creation_info
                )
        case KernelCancelledAnycastEvent():
            log.warning(f"Kernel cancelled, {event.reason = }")


async def handle_kernel_termination_lifecycle(
    context: AgentRegistry,
    source: AgentId,
    event: KernelTerminatingAnycastEvent | KernelTerminatedAnycastEvent,
) -> None:
    match event:
        case KernelTerminatingAnycastEvent():
            # `destroy_kernel()` has already changed the kernel status to "TERMINATING".
            pass
        case KernelTerminatedAnycastEvent(kernel_id, session_id, reason, exit_code):
            async with context.db.connect() as db_conn:
                await context.mark_kernel_terminated(
                    db_conn, kernel_id, session_id, reason, exit_code
                )


async def handle_kernel_heartbeat(
    context: AgentRegistry,
    source: AgentId,
    event: KernelHeartbeatEvent,
) -> None:
    await context.mark_kernel_heartbeat(event.kernel_id)


async def handle_session_creation_lifecycle(
    context: AgentRegistry,
    source: AgentId,
    event: SessionStartedAnycastEvent | SessionCancelledAnycastEvent,
) -> None:
    """
    Update the database according to the session-level lifecycle events
    published by the manager.
    """
    if event.creation_id not in context.session_creation_tracker:
        return
    log.debug("handle_session_creation_lifecycle: ev:{} s:{}", event.event_name(), event.session_id)
    if isinstance(event, SessionStartedAnycastEvent):
        if tracker := context.session_creation_tracker.get(event.creation_id):
            tracker.set()
    elif isinstance(event, SessionCancelledAnycastEvent):
        if tracker := context.session_creation_tracker.get(event.creation_id):
            tracker.set()

    await invoke_session_callback(context, source, event)
    if event.creation_id in context.session_creation_tracker:
        del context.session_creation_tracker[event.creation_id]


async def handle_session_termination_lifecycle(
    context: AgentRegistry,
    agent_id: AgentId,
    event: SessionTerminatingAnycastEvent | SessionTerminatedAnycastEvent,
) -> None:
    """
    Update the database according to the session-level lifecycle events
    published by the manager.
    """
    match event:
        case SessionTerminatingAnycastEvent():
            pass
        case SessionTerminatedAnycastEvent(session_id=session_id):
            await context.clean_session(session_id)

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
    event: ModelServiceStatusAnycastEvent,
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

    async def _update() -> None:
        async with context.db.begin_session() as db_sess:
            data: dict[str, Any] = {}
            match event.new_status:
                case ModelServiceStatus.HEALTHY:
                    data["status"] = RouteStatus.HEALTHY
                case ModelServiceStatus.UNHEALTHY:
                    data["status"] = RouteStatus.UNHEALTHY
            query = sa.update(RoutingRow).values(data).where(RoutingRow.id == route.id)
            await db_sess.execute(query)

    await execute_with_retry(_update)


async def invoke_session_callback(
    context: AgentRegistry,
    source: AgentId,
    event: (
        SessionEnqueuedAnycastEvent
        | SessionScheduledAnycastEvent
        | SessionPreparingAnycastEvent
        | SessionStartedAnycastEvent
        | SessionCancelledAnycastEvent
        | SessionTerminatingAnycastEvent
        | SessionTerminatedAnycastEvent
        | SessionSuccessAnycastEvent
        | SessionFailureAnycastEvent
    ),
) -> None:
    log.info("INVOKE_SESSION_CALLBACK (source:{}, event:{})", source, event)
    try:
        allow_stale = isinstance(
            event, (SessionCancelledAnycastEvent, SessionTerminatedAnycastEvent)
        )
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
                async with context.db.begin_session() as db_sess:
                    route = await RoutingRow.get_by_session(db_sess, session.id, load_endpoint=True)
                    endpoint = await EndpointRow.get(db_sess, route.endpoint, load_routes=True)
                    match event:
                        case SessionCancelledAnycastEvent():
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
                        case SessionTerminatedAnycastEvent():
                            query = sa.delete(RoutingRow).where(RoutingRow.id == route.id)
                            await db_sess.execute(query)
                        case SessionStartedAnycastEvent() | SessionTerminatingAnycastEvent():
                            target_kernels = await KernelRow.batch_load_by_session_id(
                                db_sess,
                                [
                                    r.session_id
                                    for r in endpoint.routings
                                    if r.status in RouteStatus.active_route_statuses()
                                ],
                            )
                            connection_info: defaultdict[str, dict[str, tuple[str, int]]] = (
                                defaultdict()
                            )
                            for kernel in target_kernels:
                                for port_info in kernel.service_ports:
                                    if port_info["is_inference"]:
                                        connection_info[port_info["name"]][str(kernel.id)] = (
                                            kernel.kernel_host,
                                            port_info["host_ports"][0],
                                        )
                            await context.valkey_live.delete_key(
                                f"endpoint.{endpoint.id}.route_connection_info"
                            )
                            await context.valkey_live.store_live_data(
                                f"endpoint.{endpoint.id}.route_connection_info",
                                json.dumps(connection_info),
                                ex=3600,
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
                    if endpoint.replicas == healthy_routes:
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
        "event": event.event_name().removeprefix("session_"),
        "session_id": str(event.session_id),
        "when": datetime.now(tzutc()).isoformat(),
    }

    context.webhook_ptask_group.create_task(
        _make_session_callback(data, callback_url),
    )


async def handle_batch_result(
    context: AgentRegistry,
    source: AgentId,
    event: SessionSuccessAnycastEvent | SessionFailureAnycastEvent,
) -> None:
    """
    Update the database according to the batch-job completion results
    """
    match event:
        case SessionSuccessAnycastEvent(session_id=session_id, reason=reason, exit_code=exit_code):
            await SessionRow.set_session_result(context.db, session_id, True, exit_code)
        case SessionFailureAnycastEvent(session_id=session_id, reason=reason, exit_code=exit_code):
            await SessionRow.set_session_result(context.db, session_id, False, exit_code)
    async with context.db.begin_session() as db_sess:
        try:
            session = await SessionRow.get_session(
                db_sess, event.session_id, kernel_loading_strategy=KernelLoadingStrategy.ALL_KERNELS
            )
        except SessionNotFound:
            return
    await context.destroy_session(
        session,
        reason=reason,
    )

    await invoke_session_callback(context, source, event)


async def handle_agent_images_remove(
    context: AgentRegistry,
    source: AgentId,
    event: AgentImagesRemoveEvent,
) -> None:
    await context.handle_agent_images_remove(source, event.image_canonicals)


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


async def handle_route_creation(
    context: AgentRegistry,
    source: AgentId,
    event: RouteCreatedAnycastEvent,
) -> None:
    endpoint: EndpointRow | None = None

    try:
        async with context.db.begin_readonly_session() as db_sess:
            log.debug("Route ID: {}", event.route_id)
            route = await RoutingRow.get(db_sess, event.route_id)
            endpoint = await EndpointRow.get(
                db_sess, route.endpoint, load_image=True, load_model=True
            )

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

            image_row = await ImageRow.resolve(
                db_sess,
                [
                    ImageIdentifier(endpoint.image_row.name, endpoint.image_row.architecture),
                    ImageAlias(endpoint.image_row.name),
                ],
            )

            environ = dict(endpoint.environ or {})
            if "BACKEND_MODEL_NAME" not in environ:
                environ["BACKEND_MODEL_NAME"] = endpoint.model_row.name

            await context.create_session(
                f"{endpoint.name}-{str(event.route_id)}",
                image_row.image_ref,
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
                    "environ": environ,
                    "scaling_group": endpoint.resource_group,
                    "resources": endpoint.resource_slots,
                    "resource_opts": endpoint.resource_opts,
                    "preopen_ports": None,
                    "agent_list": None,
                },
                ClusterMode(endpoint.cluster_mode),
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
