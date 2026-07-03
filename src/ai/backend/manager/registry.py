from __future__ import annotations

import asyncio
import base64
import itertools
import logging
import secrets
import uuid
from collections.abc import (
    Mapping,
    MutableMapping,
    Sequence,
)
from datetime import datetime, timedelta
from decimal import Decimal
from typing import (
    Any,
    cast,
)

import aiodocker
import aiotools
import sqlalchemy as sa
import yarl
from async_timeout import timeout as _timeout
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dateutil.parser import isoparse
from dateutil.tz import tzutc
from sqlalchemy.ext.asyncio import AsyncConnection as SAConnection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload, selectinload
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
from ai.backend.common.dto.agent.response import (
    CodeCompletionResp,
    DeviceHardwareInfo,
    PurgeImageResp,
    PurgeImagesResp,
)
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.types import (
    EndpointTagsModel,
    SessionTagsModel,
    TagsModel,
)
from ai.backend.common.dto.manager.rpc_request import PurgeImagesReq
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.session.broadcast import (
    SchedulingBroadcastEvent,
)
from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.common.events.hub.propagators.cache import WithCachePropagator
from ai.backend.common.events.types import EventCacheDomain, EventDomain
from ai.backend.common.exception import AliasResolutionFailed
from ai.backend.common.identifier.domain import DomainName
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.project import ProjectID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import (
    AbuseReport,
    AccessKey,
    AgentId,
    BinarySize,
    ClusterMode,
    ClusterSSHKeyPair,
    CommitStatus,
    DeviceId,
    HardwareMetadata,
    ImageAlias,
    ImageRegistry,
    KernelEnqueueingConfig,
    KernelId,
    MountInfoEntry,
    MountPermission,
    ResourceSlot,
    ResourceSlotEntry,
    SessionEnqueueingConfig,
    SessionId,
    SessionTypes,
    SlotName,
)
from ai.backend.common.utils import str_to_timedelta
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.clients.appproxy.types import CreateEndpointRequestBody
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.model_serving.types import EndpointData
from ai.backend.manager.data.session.draft import (
    KernelExecutionSpecDraft,
    KernelGroupDraft,
    SchedulingTargetDraft,
    SessionClassificationDraft,
    SessionIdentityDraft,
    SessionNetworkDraft,
    SessionOptionsDraft,
    SessionScopeDraft,
    SessionSpecDraft,
)
from ai.backend.manager.data.session.options import (
    InternalDataExtras,
    ResourceOpts,
    SessionHandlerOptions,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.models.resource_slot import ResourceAllocationRow
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.resource_slot import ResourceSlotRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController
from ai.backend.manager.sokovan.scheduling_controller.resource_parse import parse_quantity

from .agent_cache import AgentRPCCache
from .clients.agent import AgentClientPool
from .clients.appproxy.client import AppProxyClient
from .defs import DEFAULT_IMAGE_ARCH, DEFAULT_ROLE
from .errors.api import InvalidAPIParameters
from .errors.image import ImageNotFound
from .errors.kernel import (
    InvalidKernelConfig,
    SessionAlreadyExists,
    SessionNotFound,
    TooManySessionsMatched,
)
from .errors.resource import (
    AgentNotAllocated,
    DatabaseConnectionUnavailable,
    InstanceNotFound,
    NoCurrentTaskContext,
    ScalingGroupNotFound,
    ScalingGroupSessionTypeNotAllowed,
)
from .models.agent import AgentRow, agents
from .models.domain import domains
from .models.endpoint import EndpointRow
from .models.image import (
    ImageRow,
)
from .models.kernel import (
    AGENT_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    USER_RESOURCE_OCCUPYING_KERNEL_STATUSES,
    KernelRow,
    kernels,
)
from .models.keypair import query_bootstrap_script
from .models.network import NetworkRow, NetworkType
from .models.runtime_variant.row import RuntimeVariantRow
from .models.scaling_group import query_allowed_sgroups, scaling_groups
from .models.session import (
    PRIVATE_SESSION_TYPES,
    USER_RESOURCE_OCCUPYING_SESSION_STATUSES,
    ConcurrencyUsed,
    KernelLoadingStrategy,
    SessionRow,
    handle_session_exception,
)
from .models.storage import StorageSessionManager
from .models.user import UserRow
from .models.utils import (
    ExtendedAsyncSAEngine,
    execute_with_retry,
    reenter_txn_session,
)
from .models.vfolder import (
    verify_vfolder_name,
)
from .types import UserScope

type MSetType = Mapping[str | bytes, bytes | float | int | str]
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
    _scheduler_repository: SchedulerRepository
    _event_hub: EventHub

    session_creation_tracker: dict[str, asyncio.Event]
    pending_waits: set[asyncio.Task[None]]
    database_ptask_group: aiotools.PersistentTaskGroup
    webhook_ptask_group: aiotools.PersistentTaskGroup
    _client_pool: ClientPool
    _agent_client_pool: AgentClientPool

    @staticmethod
    def _mount_entries_from_creation_config(
        creation_config: Mapping[str, Any],
    ) -> tuple[MountInfoEntry, ...]:
        """Project legacy ``creation_config`` mount dict keys into typed
        :class:`MountInfoEntry` tuples.

        Reads UUID-keyed ``mount_ids`` / ``mount_id_map`` / ``mount_options``
        (modern v1 session-service path). Name-keyed ``mounts`` entries
        are not handled here — :class:`SessionService` resolves those into
        the UUID-keyed buckets upstream before any code in this module
        runs.
        """
        mount_ids = creation_config.get("mount_ids") or []
        mount_id_map: Mapping[Any, str] = creation_config.get("mount_id_map") or {}
        mount_options: Mapping[Any, Mapping[str, Any]] = creation_config.get("mount_options") or {}

        entries: list[MountInfoEntry] = []
        for raw_id in mount_ids:
            try:
                vfolder_uuid = uuid.UUID(str(raw_id))
            except (ValueError, TypeError):
                continue
            opts = mount_options.get(raw_id) or mount_options.get(vfolder_uuid) or {}
            raw_perm = opts.get("permission")
            perm: MountPermission | None = None
            if isinstance(raw_perm, MountPermission):
                perm = raw_perm
            elif isinstance(raw_perm, str):
                try:
                    perm = MountPermission(raw_perm)
                except ValueError:
                    perm = None
            raw_subpath = opts.get("subpath")
            subpath_value = str(raw_subpath) if raw_subpath is not None else None
            dst_path = mount_id_map.get(vfolder_uuid) or mount_id_map.get(raw_id)
            entries.append(
                MountInfoEntry(
                    vfolder_id=VFolderUUID(vfolder_uuid),
                    mount_destination=dst_path,
                    mount_perm=perm,
                    subpath=subpath_value,
                )
            )
        return tuple(entries)

    @staticmethod
    def _resource_entries_from_legacy_dict(
        resources: Mapping[str, Any],
    ) -> tuple[ResourceSlotEntry, ...]:
        """Project a legacy ``{slot_name: quantity}`` dict into the typed
        :class:`ResourceSlotEntry` tuple the draft expects.

        Legacy callers may hand in BinarySize shortcuts (``"512m"``,
        ``"1g"``) for memory-like slots; normalise them to plain decimal
        strings so downstream ``Decimal(quantity)`` calls in the scheduler
        and ``ResourceSlotEntry.to_resource_slot`` keep working unchanged.
        """
        if not resources:
            return ()
        return tuple(
            ResourceSlotEntry(resource_type=str(k), quantity=str(parse_quantity(v)))
            for k, v in resources.items()
        )

    def __init__(
        self,
        config_provider: ManagerConfigProvider,
        db: ExtendedAsyncSAEngine,
        agent_cache: AgentRPCCache,
        agent_client_pool: AgentClientPool,
        valkey_stat: ValkeyStatClient,
        valkey_live: ValkeyLiveClient,
        valkey_image: ValkeyImageClient,
        event_producer: EventProducer,
        event_hub: EventHub,
        storage_manager: StorageSessionManager,
        hook_plugin_ctx: HookPluginContext,
        network_plugin_ctx: NetworkPluginContext,
        scheduling_controller: SchedulingController,
        scheduler_repository: SchedulerRepository,
        *,
        debug: bool = False,
        manager_public_key: PublicKey,
        manager_secret_key: SecretKey,
    ) -> None:
        self.config_provider = config_provider
        self.docker = aiodocker.Docker()
        self.db = db
        self.agent_cache = agent_cache
        self._agent_client_pool = agent_client_pool
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
        self._scheduler_repository = scheduler_repository
        self.debug = debug
        self.rpc_keepalive_timeout = int(config_provider.config.network.rpc.keepalive_timeout)
        self.rpc_auth_manager_public_key = manager_public_key
        self.rpc_auth_manager_secret_key = manager_secret_key
        self._client_pool = ClientPool(tcp_client_session_factory)

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

    async def get_instance(self, inst_id: AgentId) -> AgentId:
        """Verify that the agent exists and return its ID."""
        async with self.db.begin_readonly_session() as db_sess:
            query = sa.select(AgentRow.id).where(AgentRow.id == inst_id)
            result = await db_sess.execute(query)
            row = result.scalar_one_or_none()
            if row is None:
                raise InstanceNotFound(inst_id)
            return AgentId(row)

    async def enumerate_instances(self, check_shadow: bool = True) -> list[AgentId]:
        """Return list of all agent IDs."""
        async with self.db.begin_readonly_session() as db_sess:
            query = sa.select(AgentRow.id)
            if check_shadow:
                query = query.where(AgentRow.status == AgentStatus.ALIVE)
            result = await db_sess.execute(query)
            return [AgentId(row) for row in result.scalars().all()]

    async def update_instance(self, inst_id: AgentId, updated_fields: dict[str, Any]) -> None:
        async def _update() -> None:
            async with self.db.begin() as conn:
                query = sa.update(agents).values(**updated_fields).where(agents.c.id == inst_id)
                await conn.execute(query)

        await execute_with_retry(_update)

    async def gather_agent_hwinfo(self, instance_id: AgentId) -> list[DeviceHardwareInfo]:
        agent_id = await self.get_instance(instance_id)
        async with self._agent_client_pool.acquire(agent_id) as client:
            result = await client.gather_hwinfo()
        return result.devices

    async def gather_storage_hwinfo(self, vfolder_host: str) -> HardwareMetadata:
        proxy_name, volume_name = self.storage_manager.get_proxy_and_volume(vfolder_host)
        manager_client = self.storage_manager.get_manager_facing_client(proxy_name)
        result = await manager_client.get_volume_hwinfo(volume_name)
        return check_type(result, HardwareMetadata)

    async def scan_gpu_alloc_map(self, instance_id: AgentId) -> Mapping[str, Any]:
        agent_id = await self.get_instance(instance_id)
        async with self._agent_client_pool.acquire(agent_id) as client:
            return await client.scan_gpu_alloc_map()

    async def _wait_for_session_running(
        self,
        session_id: SessionId,
        propagator: WithCachePropagator,
        max_wait: int,
    ) -> None:
        cache_id = EventCacheDomain.SESSION_SCHEDULER.cache_id(str(session_id))
        timeout_seconds = max_wait if max_wait > 0 else DEFAULT_WAIT_TIMEOUT_SECONDS
        while True:
            try:
                with _timeout(timeout_seconds):
                    async for event in propagator.receive(cache_id):
                        if isinstance(event, SchedulingBroadcastEvent):
                            if event.status_transition == str(SessionStatus.RUNNING):
                                return
                            if event.status_transition in (
                                str(SessionStatus.TERMINATED),
                                str(SessionStatus.CANCELLED),
                            ):
                                raise SessionNotFound("Session terminated during scheduling")
            except TimeoutError as e:
                if max_wait > 0:
                    raise e
                async with self.db.begin_readonly_session() as db_session:
                    query = sa.select(SessionRow.status).where(SessionRow.id == session_id)
                    result = await db_session.execute(query)
                    row = result.first()

                    if row is None:
                        raise SessionNotFound(f"Session {session_id} not found") from e

                    if row.status == SessionStatus.RUNNING:
                        return
                    if row.status in (SessionStatus.TERMINATED, SessionStatus.CANCELLED):
                        raise SessionNotFound("Session terminated during scheduling") from e

    async def create_session(
        self,
        session_name: str,
        image_ref: ImageRef,
        user_scope: UserScope,
        owner_access_key: AccessKey,
        resource_policy: dict[str, Any],
        session_type: SessionTypes,
        config: dict[str, Any],
        cluster_mode: ClusterMode,
        cluster_size: int,
        dry_run: bool = False,
        reuse: bool = False,
        enqueue_only: bool = False,
        max_wait_seconds: int = 0,
        priority: int = SESSION_PRIORITY_DEFAULT,
        is_preemptible: bool = True,
        bootstrap_script: str | None = None,
        dependencies: list[uuid.UUID] | None = None,
        startup_command: str | None = None,
        starts_at_timestamp: str | None = None,
        batch_timeout: timedelta | None = None,
        tag: str | None = None,
        callback_url: yarl.URL | None = None,
        route_id: uuid.UUID | None = None,
        sudo_session_enabled: bool = False,
    ) -> Mapping[str, Any]:
        log.debug("create_session():")
        resp: MutableMapping[str, Any] = {}

        current_task = asyncio.current_task()
        if current_task is None:
            raise NoCurrentTaskContext("No current task context")

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

        for alias_name in alias_folders:
            if not isinstance(alias_name, str):
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
                raise InvalidAPIParameters(f"Invalid resource allocation: {e}") from e

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
                        sa.select(domains.c.allowed_docker_registries)
                        .select_from(domains)
                        .where(domains.c.name == user_scope.domain_name)
                    )
                    allowed_registries = await conn.scalar(query)
                    if allowed_registries is None or image_ref.registry not in allowed_registries:
                        raise AliasResolutionFailed
        except AliasResolutionFailed as e:
            raise ImageNotFound("unknown alias or disallowed registry") from e

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
                if sess.main_kernel.image is None:
                    raise InvalidKernelConfig("Session main kernel has no image specified")
                if sess.main_kernel.architecture is None:
                    raise InvalidKernelConfig("Session main kernel has no architecture specified")
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

        starts_at: datetime | None = None
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
            if conn is None:
                raise DatabaseConnectionUnavailable("Database connection not available")
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
                        is_preemptible=is_preemptible,
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
                        startup_command=startup_command,
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
                except TimeoutError:
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
                    if row is None:
                        raise SessionNotFound(f"Session kernel not found: {session_id}")
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
        resource_policy: dict[str, Any],
        scaling_group: str,
        sess_type: SessionTypes,
        tag: str,
        enqueue_only: bool = False,
        max_wait_seconds: int = 0,
        sudo_session_enabled: bool = False,
        attach_network: uuid.UUID | None = None,
    ) -> Mapping[str, Any]:
        resp: MutableMapping[str, Any] = {}

        current_task = asyncio.current_task()
        if current_task is None:
            raise NoCurrentTaskContext("No current task context")

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

        if _mounts := template["spec"].get("mounts"):
            mounts = list(_mounts.keys())
            mount_map = {key: value for (key, value) in _mounts.items() if len(value) > 0}
        if _environ := template["spec"].get("environ"):
            environ = _environ

        kernel_configs: list[KernelEnqueueingConfig] = []
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
                        sa.select(domains.c.allowed_docker_registries)
                        .select_from(domains)
                        .where(domains.c.name == user_scope.domain_name)
                    )
                    allowed_registries = await conn.scalar(query)
                    if (
                        allowed_registries is None
                        or requested_image_ref.registry not in allowed_registries
                    ):
                        raise AliasResolutionFailed
                    kernel_config["image_ref"] = requested_image_ref
            except AliasResolutionFailed as e:
                raise ImageNotFound("unknown alias or disallowed registry") from e

            for i in range(node["replicas"]):
                kernel_config["cluster_idx"] = i + 1
                kernel_configs.append(
                    check_type(kernel_config, KernelEnqueueingConfig),
                )

        session_creation_id = secrets.token_urlsafe(16)
        kernel_id: KernelId | None = None
        current_task = asyncio.current_task()
        if current_task is None:
            raise NoCurrentTaskContext("No current task context")

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
                except TimeoutError:
                    resp["status"] = "TIMEOUT"
                else:
                    await asyncio.sleep(0.5)
                    async with self.db.begin_readonly() as conn:
                        query = (
                            sa.select(
                                kernels.c.status,
                                kernels.c.service_ports,
                            )
                            .select_from(kernels)
                            .where(kernels.c.id == kernel_id)
                        )
                        result = await conn.execute(query)
                        row = result.first()
                    if row is None:
                        raise SessionNotFound(f"Kernel not found: {kernel_id}")
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

    async def _enqueue_session_via_sokovan(
        self,
        session_creation_id: str,
        session_name: str,
        access_key: AccessKey,
        session_enqueue_configs: SessionEnqueueingConfig,
        scaling_group: str | None,
        session_type: SessionTypes,
        resource_policy: dict[str, Any],
        *,
        user_scope: UserScope,
        priority: int,
        public_sgroup_only: bool,
        cluster_mode: ClusterMode,
        cluster_size: int,
        session_tag: str | None,
        internal_data: dict[str, Any] | None,
        starts_at: datetime | None,
        batch_timeout: timedelta | None,
        agent_list: Sequence[str] | None,
        dependency_sessions: Sequence[SessionId] | None,
        callback_url: URL | None,
        route_id: uuid.UUID | None,
        sudo_session_enabled: bool,
        network: NetworkRow | None,
        startup_command: str | None,
        is_preemptible: bool,
    ) -> SessionId:
        """Enqueue session via the Sokovan draft path.

        Legacy v1 REST/GraphQL surface: receives already-expanded
        ``kernel_configs`` (one per replica) inside ``session_enqueue_configs``
        and the session-level ``creation_config`` dict. Groups the
        per-replica configs by ``cluster_role`` into
        :class:`KernelGroupDraft` entries before handing the draft to
        the scheduling controller.
        """
        kernel_enqueue_configs: list[KernelEnqueueingConfig] = session_enqueue_configs[
            "kernel_configs"
        ]
        creation_config: dict[str, Any] = session_enqueue_configs["creation_config"]

        # Legacy name-keyed ``mounts`` are resolved into UUID-keyed buckets
        # upstream in ``SessionService`` (via ``VFolderProcessors``), so by
        # the time control reaches here the config carries only ``mount_ids``
        # / ``mount_id_map`` / ``mount_options``.
        mount_entries = self._mount_entries_from_creation_config(creation_config)
        resource_entries = self._resource_entries_from_legacy_dict(
            creation_config.get("resources") or {}
        )
        resource_opts = ResourceOpts.model_validate(creation_config.get("resource_opts") or {})
        environ_dict = dict(creation_config.get("environ") or {})
        preopen_ports = tuple(creation_config.get("preopen_ports") or ())
        # Session-level fields (callback, dependencies, etc.) flow onto
        # the draft directly. ``agent_list`` maps onto the scheduling
        # target's designated agents.
        dependencies = tuple(SessionID(dep_id) for dep_id in (dependency_sessions or ()))
        network_id = str(network.id) if network is not None else None
        batch_timeout_sec = (
            int(batch_timeout.total_seconds()) if batch_timeout is not None else None
        )

        # Project legacy per-replica configs into ``KernelGroupDraft``
        # instances. Two distinct legacy shapes need to survive this
        # transition; both get mapped to the same ``main``/``sub``
        # layout the old ``ClusterConfigurationRule`` produced so rows
        # written on the new path stay wire/DB-compatible with the
        # historical data (``cluster_role`` values of ``main`` + ``sub``,
        # hostnames ``main1`` + ``sub1..subN-1``):
        #
        #   (a) ``create_session`` path: one kernel_config entry and a
        #       separate ``cluster_size`` parameter. When size > 1 the
        #       old rule auto-expanded into 1 ``main`` + (N-1) ``sub``
        #       kernels; ``replica_count`` on a single draft group would
        #       instead produce N ``main`` kernels, which breaks queries
        #       filtering on ``cluster_role='sub'``.
        #
        #   (b) ``create_cluster`` path: multiple kernel_configs already
        #       expanded per replica with ``cluster_role`` set per
        #       entry. These just need to be grouped by role.
        #
        # Legacy ``KernelEnqueueingConfig`` carries an ``ImageRef`` only,
        # so resolve it to ``ImageID`` here and hand the id down to the
        # controller — the scheduler repository expects spec drafts with
        # ``image_id`` already populated (task #29 migrates the read path
        # to persist ``ImageID`` end-to-end).
        image_id_by_ref: dict[ImageRef, ImageID] = {}
        async with self.db.begin_readonly_session() as db_sess:
            for kernel in kernel_enqueue_configs:
                image_ref = kernel["image_ref"]
                if image_ref in image_id_by_ref:
                    continue
                image_row = await ImageRow.resolve(db_sess, [image_ref])
                image_id_by_ref[image_ref] = ImageID(image_row.id)

        def _build_execution_spec(
            kernel: KernelEnqueueingConfig,
        ) -> KernelExecutionSpecDraft:
            return KernelExecutionSpecDraft(
                image_id=image_id_by_ref[kernel["image_ref"]],
                resources=resource_entries,
                resource_opts=resource_opts,
                environ=environ_dict,
                mounts=mount_entries,
                startup_command=kernel.get("startup_command") or startup_command,
                bootstrap_script=kernel.get("bootstrap_script") or None,
                starts_at=starts_at,
                batch_timeout_sec=batch_timeout_sec,
            )

        groups_by_role: dict[str, KernelGroupDraft] = {}
        if len(kernel_enqueue_configs) == 1 and cluster_size > 1:
            # Shape (a): auto-expand to 1 main + (cluster_size-1) sub.
            only_kernel = kernel_enqueue_configs[0]
            execution_spec = _build_execution_spec(only_kernel)
            groups_by_role[DEFAULT_ROLE] = KernelGroupDraft(
                role=DEFAULT_ROLE,
                replica_count=1,
                preopen_ports=preopen_ports,
                execution_spec=execution_spec,
            )
            groups_by_role["sub"] = KernelGroupDraft(
                role="sub",
                replica_count=cluster_size - 1,
                preopen_ports=preopen_ports,
                execution_spec=execution_spec,
            )
        else:
            # Shape (b): each config already corresponds to one replica;
            # group by the caller-supplied ``cluster_role``. Preserve the
            # legacy "idx==0 → main, idx>0 → sub" fallback for entries
            # that omit ``cluster_role`` entirely.
            for idx, kernel in enumerate(kernel_enqueue_configs):
                role = kernel.get("cluster_role") or (DEFAULT_ROLE if idx == 0 else "sub")
                existing = groups_by_role.get(role)
                if existing is None:
                    groups_by_role[role] = KernelGroupDraft(
                        role=role,
                        replica_count=1,
                        preopen_ports=preopen_ports,
                        execution_spec=_build_execution_spec(kernel),
                    )
                else:
                    groups_by_role[role] = existing.model_copy(
                        update={"replica_count": existing.replica_count + 1}
                    )

        if not groups_by_role:
            raise InvalidAPIParameters("No kernel groups resolved from the enqueue request.")

        if scaling_group:
            resource_group_name = ResourceGroupName(scaling_group)
        else:
            resource_group_id = await self._scheduler_repository.pick_default_resource_group(
                access_key=access_key,
                domain_name=user_scope.domain_name,
                project_id=ProjectID(user_scope.group_id),
            )
            resource_group_name = await self._scheduler_repository.get_resource_group_name_by_id(
                resource_group_id
            )

        draft = SessionSpecDraft(
            identity=SessionIdentityDraft(
                session_id=SessionID(uuid.uuid4()),
                creation_id=session_creation_id,
                session_name=session_name,
                access_key=access_key,
                user_uuid=user_scope.user_uuid,
            ),
            scope=SessionScopeDraft(
                domain_name=DomainName(user_scope.domain_name),
                project_id=ProjectID(user_scope.group_id),
                resource_group_name=resource_group_name,
            ),
            classification=SessionClassificationDraft(
                session_type=session_type,
                tag=session_tag,
            ),
            network=SessionNetworkDraft(network_id=network_id),
            callback_url=callback_url,
            dependencies=dependencies,
            options=SessionOptionsDraft(
                priority=priority,
                is_preemptible=is_preemptible,
                cluster_mode=cluster_mode,
                cluster_size=cluster_size,
                scheduling_target=SchedulingTargetDraft(
                    designated_agents=tuple(AgentId(a) for a in (agent_list or ())),
                ),
                kernel_groups=tuple(groups_by_role.values()),
                handler_options=SessionHandlerOptions(),
            ),
            internal_data_extras=InternalDataExtras(
                sudo_session_enabled=sudo_session_enabled,
            ),
        )

        return await self._scheduling_controller.enqueue_session_from_draft(draft)

    async def enqueue_session(
        self,
        session_creation_id: str,
        session_name: str,
        access_key: AccessKey,
        session_enqueue_configs: SessionEnqueueingConfig,
        scaling_group: str | None,
        session_type: SessionTypes,
        resource_policy: dict[str, Any],
        *,
        user_scope: UserScope,
        priority: int = SESSION_PRIORITY_DEFAULT,
        is_preemptible: bool = True,
        public_sgroup_only: bool = True,
        cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE,
        cluster_size: int = 1,
        session_tag: str | None = None,
        internal_data: dict[str, Any] | None = None,
        starts_at: datetime | None = None,
        batch_timeout: timedelta | None = None,
        agent_list: Sequence[str] | None = None,
        dependency_sessions: Sequence[SessionId] | None = None,
        callback_url: URL | None = None,
        route_id: uuid.UUID | None = None,
        sudo_session_enabled: bool = False,
        network: NetworkRow | None = None,
        startup_command: str | None = None,
    ) -> SessionId:
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
            is_preemptible=is_preemptible,
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
            startup_command=startup_command,
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
                total_allocs: list[Decimal] = []
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

    async def get_user_occupancy(
        self, user_id: uuid.UUID, *, db_sess: AsyncSession | None = None
    ) -> ResourceSlot:
        known_slot_types = await self.config_provider.legacy_etcd_config_loader.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                ra = ResourceAllocationRow.__table__
                k = KernelRow.__table__
                effective = sa.func.coalesce(ra.c.used, ra.c.requested)
                query = (
                    sa.select(ra.c.slot_name, sa.func.sum(effective).label("total"))
                    .select_from(ra.join(k, ra.c.kernel_id == k.c.id))
                    .where(
                        k.c.user_uuid == user_id,
                        k.c.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES),
                        k.c.session_type.not_in(PRIVATE_SESSION_TYPES),
                        ra.c.free_at.is_(None),
                    )
                    .group_by(ra.c.slot_name)
                )
                rows = (await _sess.execute(query)).all()
                return ResourceSlot({
                    r.slot_name: r.total for r in rows if r.slot_name in known_slot_types
                })

        return await execute_with_retry(_query)

    async def get_keypair_occupancy(
        self, access_key: AccessKey, *, db_sess: AsyncSession | None = None
    ) -> ResourceSlot:
        known_slot_types = await self.config_provider.legacy_etcd_config_loader.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                ra = ResourceAllocationRow.__table__
                k = KernelRow.__table__
                effective = sa.func.coalesce(ra.c.used, ra.c.requested)
                query = (
                    sa.select(ra.c.slot_name, sa.func.sum(effective).label("total"))
                    .select_from(ra.join(k, ra.c.kernel_id == k.c.id))
                    .where(
                        k.c.access_key == access_key,
                        k.c.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES),
                        k.c.session_type.not_in(PRIVATE_SESSION_TYPES),
                        ra.c.free_at.is_(None),
                    )
                    .group_by(ra.c.slot_name)
                )
                rows = (await _sess.execute(query)).all()
                return ResourceSlot({
                    r.slot_name: r.total for r in rows if r.slot_name in known_slot_types
                })

        return await execute_with_retry(_query)

    async def get_domain_occupancy(
        self, domain_name: str, *, db_sess: AsyncSession | None = None
    ) -> ResourceSlot:
        known_slot_types = await self.config_provider.legacy_etcd_config_loader.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                ra = ResourceAllocationRow.__table__
                k = KernelRow.__table__
                effective = sa.func.coalesce(ra.c.used, ra.c.requested)
                query = (
                    sa.select(ra.c.slot_name, sa.func.sum(effective).label("total"))
                    .select_from(ra.join(k, ra.c.kernel_id == k.c.id))
                    .where(
                        k.c.domain_name == domain_name,
                        k.c.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES),
                        k.c.session_type.not_in(PRIVATE_SESSION_TYPES),
                        ra.c.free_at.is_(None),
                    )
                    .group_by(ra.c.slot_name)
                )
                rows = (await _sess.execute(query)).all()
                return ResourceSlot({
                    r.slot_name: r.total for r in rows if r.slot_name in known_slot_types
                })

        return await execute_with_retry(_query)

    async def get_group_occupancy(
        self, group_id: uuid.UUID, *, db_sess: AsyncSession | None = None
    ) -> ResourceSlot:
        known_slot_types = await self.config_provider.legacy_etcd_config_loader.get_resource_slots()

        async def _query() -> ResourceSlot:
            async with reenter_txn_session(self.db, db_sess) as _sess:
                ra = ResourceAllocationRow.__table__
                k = KernelRow.__table__
                effective = sa.func.coalesce(ra.c.used, ra.c.requested)
                query = (
                    sa.select(ra.c.slot_name, sa.func.sum(effective).label("total"))
                    .select_from(ra.join(k, ra.c.kernel_id == k.c.id))
                    .where(
                        k.c.group_id == group_id,
                        k.c.status.in_(USER_RESOURCE_OCCUPYING_KERNEL_STATUSES),
                        k.c.session_type.not_in(PRIVATE_SESSION_TYPES),
                        ra.c.free_at.is_(None),
                    )
                    .group_by(ra.c.slot_name)
                )
                rows = (await _sess.execute(query)).all()
                return ResourceSlot({
                    r.slot_name: r.total for r in rows if r.slot_name in known_slot_types
                })

        return await execute_with_retry(_query)

    async def update_scaling_group(self, agent_id: AgentId, scaling_group: str) -> None:
        verified_agent_id = await self.get_instance(agent_id)
        async with self._agent_client_pool.acquire(verified_agent_id) as client:
            await client.update_scaling_group(scaling_group)

    async def recalc_resource_usage(self, do_fullscan: bool = False) -> None:
        async def _recalc() -> Mapping[AccessKey, ConcurrencyUsed]:
            access_key_to_concurrency_used: dict[AccessKey, ConcurrencyUsed] = {}

            async with self.db.begin_session() as db_sess:
                # Query running containers and calculate concurrency_used per AK.
                # Agent occupied slots are now managed by the normalized
                # agent_resources table, so only concurrency tracking remains here.
                session_query = (
                    sa.select(SessionRow)
                    .where(SessionRow.status.in_(USER_RESOURCE_OCCUPYING_SESSION_STATUSES))
                    .options(
                        load_only(
                            SessionRow.id,
                            SessionRow.access_key,
                            SessionRow.status,
                            SessionRow.session_type,
                        ),
                    )
                )
                async for session_row in await db_sess.stream_scalars(session_query):
                    access_key = cast(AccessKey, session_row.access_key)
                    if access_key not in access_key_to_concurrency_used:
                        access_key_to_concurrency_used[access_key] = ConcurrencyUsed(access_key)
                    if session_row.session_type in PRIVATE_SESSION_TYPES:
                        access_key_to_concurrency_used[access_key].system_session_ids.add(
                            session_row.id
                        )
                    else:
                        access_key_to_concurrency_used[access_key].compute_session_ids.add(
                            session_row.id
                        )
            return access_key_to_concurrency_used

        access_key_to_concurrency_used = await execute_with_retry(_recalc)
        await self._update_concurrency(access_key_to_concurrency_used, do_fullscan)
        await self._reconcile_agent_resources()

    async def _reconcile_agent_resources(self) -> None:
        """Clean up orphaned allocations and reconcile agent_resources.

        Delegates to ResourceSlotRepository which runs both steps in a single
        transaction: orphan cleanup first, then drift correction.
        """
        repo = ResourceSlotRepository(self.db)
        result = await repo.reconcile_agent_resources()
        for r in result.reconciled_terminal_kernels:
            log.warning(
                "reconciled terminal-session kernel drift: kernel={}, session={}, {} -> CANCELLED",
                r.kernel_id,
                r.session_id,
                r.from_kernel_status,
            )
        for o in result.orphaned_allocations:
            log.warning(
                "freed orphaned resource allocation: kernel={}, slot={}",
                o.kernel_id,
                o.slot_name,
            )
        for d in result.agent_resource_drifts:
            log.warning(
                "agent_resources drift detected for {}:{}: tracked={}, actual={}",
                d.agent_id,
                d.slot_name,
                d.tracked,
                d.actual,
            )

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
                    agent_id = session.main_kernel.agent
                    if agent_id is None:
                        log.warning(
                            "Cannot destroy network {}: main kernel has no agent allocated",
                            network_ref_name,
                        )
                    else:
                        try:
                            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                                await client.destroy_local_network(network_ref_name)
                        except Exception:
                            log.exception(
                                "Failed to destroy the agent-local network {}", network_ref_name
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
                    log.exception("Failed to destroy the overlay network {}", network_ref_name)
            else:
                pass

    async def execute(
        self,
        session: SessionRow,
        api_version: tuple[int, str],
        run_id: str,
        mode: str,
        code: str,
        opts: Mapping[str, Any],
        *,
        flush_timeout: float | None = None,
    ) -> Mapping[str, Any]:
        async with handle_session_exception("execute"):
            # The agent aggregates at most 2 seconds of outputs
            # if the kernel runs for a long time.
            major_api_version = api_version[0]
            if major_api_version == 4:  # manager-agent protocol is same.
                major_api_version = 3
            agent_id = session.main_kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Session {session.id} main kernel has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.execute(
                    session.id,
                    session.main_kernel.id,
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
        async with handle_session_exception("trigger_batch_execution"):
            agent_id = session.main_kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Session {session.id} main kernel has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.trigger_batch_execution(
                    session.id,
                    session.main_kernel.id,
                    session.main_kernel.startup_command or "",
                    float(session.batch_timeout) if session.batch_timeout is not None else None,
                )

    async def interrupt_session(
        self,
        session: SessionRow,
    ) -> Mapping[str, Any]:
        async with handle_session_exception("execute"):
            agent_id = session.main_kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Session {session.id} main kernel has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.interrupt_kernel(session.main_kernel.id)

    async def get_completions(
        self,
        session: SessionRow,
        text: str,
        opts: Mapping[str, Any],
    ) -> CodeCompletionResp:
        async with handle_session_exception("execute"):
            # NOTE: Callosum serialize all inputs to dict and upack all array inputs to tuples
            agent_id = session.main_kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Session {session.id} main kernel has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                result = await client.get_completions(session.main_kernel.id, text, opts)
            return CodeCompletionResp.from_dict(result)

    async def start_service(
        self,
        main_kernel_id: KernelId,
        agent_id: AgentId,
        service: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        async with handle_session_exception("execute"):
            async with self._agent_client_pool.acquire(agent_id) as client:
                return await client.start_service(main_kernel_id, service, opts)

    async def shutdown_service(
        self,
        session: SessionRow,
        service: str,
    ) -> None:
        async with handle_session_exception("shutdown_service"):
            agent_id = session.main_kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Session {session.id} main kernel has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.shutdown_service(session.main_kernel.id, service)

    async def upload_file(
        self,
        session: SessionRow,
        filename: str,
        payload: bytes,
    ) -> Mapping[str, Any]:
        async with handle_session_exception("upload_file"):
            agent_id = session.main_kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Session {session.id} main kernel has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.upload_file(session.main_kernel.id, filename, payload)

    async def download_file(
        self,
        session: SessionRow,
        filepath: str,
    ) -> bytes:
        kernel = session.main_kernel
        async with handle_session_exception("download_file"):
            agent_id = kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Kernel {kernel.id} has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.download_file(kernel.id, filepath)

    async def download_single(
        self,
        session: SessionRow,
        _access_key: AccessKey,
        filepath: str,
    ) -> bytes:
        kernel = session.main_kernel
        async with handle_session_exception("download_single"):
            agent_id = kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Kernel {kernel.id} has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.download_single(kernel.id, filepath)

    async def list_files(
        self,
        session: SessionRow,
        path: str,
    ) -> Mapping[str, Any]:
        async with handle_session_exception("list_files"):
            agent_id = session.main_kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Session {session.id} main kernel has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.list_files(session.main_kernel.id, path)

    async def get_logs_from_agent(
        self,
        session: SessionRow,
        kernel_id: KernelId | None = None,
    ) -> str:
        async with handle_session_exception("get_logs_from_agent"):
            kernel = (
                session.get_kernel_by_id(kernel_id)
                if kernel_id is not None
                else session.main_kernel
            )
            if kernel.agent is None:
                raise InstanceNotFound(
                    "Kernel has not been assigned to an agent.", extra_data={"kernel_id": kernel_id}
                )
            async with self._agent_client_pool.acquire(AgentId(kernel.agent)) as client:
                reply = await client.get_logs(kernel.id)
            return reply["logs"]

    async def sync_agent_kernel_registry(self, agent_id: AgentId) -> None:
        """
        Fetch agent data and status of related kernel data from DB.
        If agent's kernel_registry has unknown kernel data,
        """

        async with self.db.begin_readonly() as db_conn:
            query = (
                sa.select(kernels.c.id, kernels.c.session_id, kernels.c.agent_addr)
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
            async with self._agent_client_pool.acquire(agent_id) as client:
                await client.sync_kernel_registry([
                    (kernel.id, kernel.session_id) for kernel in grouped_kernels
                ])
            return

    async def _get_user_email(
        self,
        kernel: KernelRow,
    ) -> str:
        async with self.db.begin_readonly() as db_conn:
            query = sa.select(UserRow.email).where(UserRow.uuid == kernel.user_uuid)
            result = await db_conn.execute(query)
            user_email = str(result.scalar())
            return user_email.replace("@", "_")

    async def get_commit_status(
        self,
        kernel_ids: Sequence[KernelId],
    ) -> Mapping[KernelId, str]:
        kernel_ids_str = [str(kernel_id) for kernel_id in kernel_ids]
        commit_statuses = await self.valkey_stat.get_kernel_commit_statuses(kernel_ids_str)

        return {
            kernel_id: str(result, "utf-8") if result is not None else CommitStatus.READY.value
            for kernel_id, result in zip(kernel_ids, commit_statuses, strict=True)
        }

    async def commit_session(
        self,
        session: SessionRow,
        new_image_ref: ImageRef,
        *,
        extra_labels: dict[str | LabelName, str] | None = None,
    ) -> Mapping[str, Any]:
        """
        Commit a main kernel's container of the given session.
        """

        if extra_labels is None:
            extra_labels = {}
        kernel: KernelRow = session.main_kernel
        if kernel.status != KernelStatus.RUNNING:
            raise InvalidAPIParameters(
                f"Unable to commit since the kernel k:{kernel.id} (of s:{session.id}) is"
                " currently not in RUNNING state."
            )
        email = await self._get_user_email(kernel)
        async with handle_session_exception("commit_session"):
            agent_id = kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Kernel {kernel.id} has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.commit(
                    kernel.id,
                    email,
                    canonical=new_image_ref.canonical,
                    extra_labels=extra_labels,
                )

    async def push_image(
        self,
        agent: AgentId,
        image_ref: ImageRef,
        registry: ImageRegistry,
    ) -> Mapping[str, Any]:
        """
        Commit a main kernel's container of the given session.
        """
        async with self._agent_client_pool.acquire(agent) as client:
            return await client.push_image(
                image_ref,
                {**registry, "url": str(registry["url"])},
            )

    async def commit_session_to_file(
        self,
        session: SessionRow,
        filename: str | None,
        extra_labels: dict[str, str] | None = None,
    ) -> Mapping[str, Any]:
        """
        Commit a main kernel's container of the given session.
        """

        if extra_labels is None:
            extra_labels = {}
        kernel: KernelRow = session.main_kernel
        if kernel.status != KernelStatus.RUNNING:
            raise InvalidAPIParameters(
                f"Unable to commit since kernel(id: {kernel.id}) of session(id: {session.id}) is"
                " currently not RUNNING."
            )
        if kernel.image is None:
            raise InvalidAPIParameters(f"Kernel image is not set for kernel {kernel.id}")
        email = await self._get_user_email(kernel)
        now = datetime.now(tzutc()).strftime("%Y-%m-%dT%HH%MM%SS")
        shortend_sname = (session.name or "")[:SESSION_NAME_LEN_LIMIT]
        registry, _, filtered = kernel.image.partition("/")
        img_path, _, image_name = filtered.partition("/")
        filename = f"{now}_{shortend_sname}_{image_name}.tar.gz"
        filename = filename.replace(":", "-")
        async with handle_session_exception("commit_session_to_file"):
            agent_id = kernel.agent
            if agent_id is None:
                raise AgentNotAllocated(f"Kernel {kernel.id} has no agent allocated")
            async with self._agent_client_pool.acquire(AgentId(agent_id)) as client:
                return await client.commit(
                    kernel.id,
                    email,
                    filename=filename,
                    extra_labels=extra_labels,
                    canonical=ImageRef.parse_image_str(kernel.image, registry).canonical,
                )

    async def get_agent_local_config(
        self,
        agent_id: AgentId,
        _agent_addr: str,
    ) -> Mapping[str, str]:
        async with self._agent_client_pool.acquire(agent_id) as client:
            return await client.get_local_config()

    async def purge_images(self, agent_id: AgentId, request: PurgeImagesReq) -> PurgeImagesResp:
        async with self._agent_client_pool.acquire(agent_id) as client:
            result = await client.purge_images(request.images, request.force, request.noprune)

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
    ) -> AbuseReport | None:
        kern_id = str(kernel_id)
        result = await self.valkey_stat.get_abuse_report(kern_id)
        if result is None:
            return None
        return {
            "kernel": kern_id,
            "abuse_report": result,
        }

    @staticmethod
    def _resolve_health_check(endpoint: EndpointData) -> ModelHealthCheck | None:
        """Pull health-check config from the endpoint's current revision.

        ``endpoint.model_definition`` is the already-merged result persisted at
        revision creation time (variant baseline → preset → yaml → request).
        The runtime path returns exactly what was stored — no dynamic
        fallback — so AppProxy never sees a config that drifts from the
        revision snapshot.
        """
        if endpoint.model_definition is None:
            return None
        return endpoint.model_definition.health_check_config()

    async def create_appproxy_endpoint(
        self,
        db_sess: AsyncSession,
        endpoint: EndpointData,
    ) -> str:
        query = (
            sa.select(scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token)
            .select_from(scaling_groups)
            .where(scaling_groups.c.name == endpoint.resource_group)
        )

        result = await db_sess.execute(query)
        sgroup = result.first()
        if sgroup is None:
            raise InvalidAPIParameters(f"Scaling group not found: {endpoint.resource_group}")
        wsproxy_addr = sgroup.wsproxy_addr
        wsproxy_api_token = sgroup.wsproxy_api_token
        wsproxy_client = self._load_app_proxy_client(wsproxy_addr, wsproxy_api_token)

        if endpoint.model is None:
            raise InvalidAPIParameters("Model not set for endpoint")

        health_check_config = self._resolve_health_check(endpoint)

        # ``EndpointData`` carries ``runtime_variant_id`` only. AppProxy's
        # wire API keys on the variant name string, so resolve the id into
        # a name at this single wire boundary rather than plumbing the
        # string through internal data types.
        variant_name = (
            await db_sess.execute(
                sa.select(RuntimeVariantRow.name).where(
                    RuntimeVariantRow.id == endpoint.runtime_variant_id
                )
            )
        ).scalar_one()

        request_body = CreateEndpointRequestBody(
            version="v2",
            service_name=endpoint.name,
            tags=TagsModel(
                session=SessionTagsModel(
                    user_uuid=str(endpoint.session_owner_id),
                    project_id=str(endpoint.project),
                    domain_name=endpoint.domain,
                ),
                endpoint=EndpointTagsModel(
                    id=str(endpoint.id),
                    runtime_variant=variant_name,
                    existing_url=str(endpoint.url) if endpoint.url else None,
                ),
            ),
            open_to_public=endpoint.open_to_public,
            health_check=health_check_config,
        )
        endpoint_json = await wsproxy_client.create_endpoint(endpoint.id, request_body)
        return cast(str, endpoint_json["endpoint"])

    async def delete_appproxy_endpoint(self, db_sess: AsyncSession, endpoint: EndpointRow) -> None:
        query = (
            sa.select(scaling_groups.c.wsproxy_addr, scaling_groups.c.wsproxy_api_token)
            .select_from(scaling_groups)
            .where(scaling_groups.c.name == endpoint.resource_group)
        )

        result = await db_sess.execute(query)
        sgroup = result.first()
        if sgroup is None:
            raise InvalidAPIParameters(f"Scaling group not found: {endpoint.resource_group}")
        wsproxy_addr = sgroup.wsproxy_addr
        wsproxy_api_token = sgroup.wsproxy_api_token

        wsproxy_client = self._load_app_proxy_client(wsproxy_addr, wsproxy_api_token)
        await wsproxy_client.delete_endpoint(endpoint.id)


async def check_scaling_group(
    conn: SAConnection,
    scaling_group: str | None,
    session_type: SessionTypes,
    access_key: AccessKey,
    domain_name: str,
    group_id: ProjectID | str,
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
        candidates = [sgroup for sgroup in candidates if sgroup.is_public]
    if not candidates:
        raise ScalingGroupNotFound("You have no scaling groups allowed to use.")

    stype = session_type.value.lower()
    if scaling_group is None:
        for sgroup in candidates:
            allowed_session_types = sgroup.scheduler_opts.allowed_session_types
            if stype in allowed_session_types:
                scaling_group = sgroup.name
                break
        else:
            raise ScalingGroupNotFound(
                f"No scaling groups accept the session type '{session_type}'.",
            )
    else:
        scaling_group_found = False
        for sgroup in candidates:
            if scaling_group == sgroup.name:
                # scaling_group's unique key is 'name' field for now,
                # but we will change scaling_group's unique key to new 'id' field.
                scaling_group_found = True
                allowed_session_types = sgroup.scheduler_opts.allowed_session_types
                if stype in allowed_session_types:
                    break
        else:
            if scaling_group_found:
                raise ScalingGroupSessionTypeNotAllowed(
                    f"The scaling group '{scaling_group}' does not accept "
                    f"the session type '{session_type}'."
                )
            raise ScalingGroupNotFound(
                f"The scaling group '{scaling_group}' does not exist "
                f"or you do not have access to the scaling group '{scaling_group}'."
            )
    if scaling_group is None:
        raise ScalingGroupNotFound("Scaling group not found")
    return scaling_group
