from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import groupby
from typing import Any, Awaitable, Optional

import async_timeout
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import (
    AgentId,
    AutoPullBehavior,
    ClusterInfo,
    ClusterMode,
    ClusterSSHKeyPair,
    ClusterSSHPortMapping,
    ImageConfig,
    KernelCreationConfig,
    KernelId,
    SessionId,
)
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.clients.agent import AgentPool
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.defs import SERVICE_MAX_RETRIES, START_SESSION_TIMEOUT_SEC
from ai.backend.manager.exceptions import convert_to_status_data
from ai.backend.manager.metrics.scheduler import (
    SchedulerPhaseMetricObserver,
)
from ai.backend.manager.models.network import NetworkType
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.repositories.scheduler import (
    SchedulerRepository,
)

from ..results import ScheduledSessionData, ScheduleResult
from ..types import (
    ImageConfigData,
    KernelBindingData,
    NetworkSetup,
    SessionDataForPull,
    SessionDataForStart,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SessionLauncherArgs:
    repository: SchedulerRepository
    agent_pool: AgentPool
    network_plugin_ctx: NetworkPluginContext
    config_provider: ManagerConfigProvider
    valkey_schedule: ValkeyScheduleClient


class SessionLauncher:
    """
    Handles the execution of prepare and start operations for sessions.

    Orchestrates:
    1. Prepare: SCHEDULED -> PREPARING (image pulling)
    2. Start: PREPARED -> CREATING (kernel creation)
    3. Retry operations for stuck sessions
    """

    _repository: SchedulerRepository
    _agent_pool: AgentPool
    _network_plugin_ctx: NetworkPluginContext
    _config_provider: ManagerConfigProvider
    _valkey_schedule: ValkeyScheduleClient
    _phase_metrics: SchedulerPhaseMetricObserver

    def __init__(self, args: SessionLauncherArgs) -> None:
        self._repository = args.repository
        self._agent_pool = args.agent_pool
        self._network_plugin_ctx = args.network_plugin_ctx
        self._config_provider = args.config_provider
        self._valkey_schedule = args.valkey_schedule
        self._phase_metrics = SchedulerPhaseMetricObserver.instance()

    async def check_preconditions(self) -> ScheduleResult:
        """
        Check preconditions for scheduled sessions.
        Transitions sessions from SCHEDULED to PREPARING and triggers image pulling.

        :return: ScheduleResult with the count of sessions transitioned
        """
        # Get scheduled sessions for image pulling
        result = await self._repository.get_sessions_for_pull(
            [SessionStatus.SCHEDULED],
            [
                KernelStatus.SCHEDULED,
            ],
        )
        scheduled_sessions = result.sessions
        image_configs = result.image_configs

        if not scheduled_sessions:
            return ScheduleResult()

        # Extract session IDs for status update
        session_ids = [s.session_id for s in scheduled_sessions]

        # Update sessions to PREPARING status
        await self._repository.update_sessions_to_preparing(session_ids)

        # Trigger image checking and pulling on agents
        await self._trigger_image_pulling_for_sessions(scheduled_sessions, image_configs)

        # Convert to ScheduledSessionData format
        scheduled_data = [
            ScheduledSessionData(
                session_id=session.session_id,
                creation_id=session.creation_id,
                access_key=session.access_key,
                reason="passed-preconditions",
            )
            for session in scheduled_sessions
        ]
        return ScheduleResult(scheduled_sessions=scheduled_data)

    async def _trigger_image_pulling_for_sessions(
        self,
        sessions: list[SessionDataForPull],
        image_configs: dict[str, ImageConfigData],
    ) -> None:
        """
        Trigger image checking and pulling on agents for the given sessions.

        :param sessions: List of sessions with kernels
        :param image_configs: Image configurations indexed by image name
        """
        auto_pull = self._config_provider.config.docker.image.auto_pull.value

        # Group kernels by agent for image pulling
        agent_image_configs: defaultdict[AgentId, dict[str, ImageConfig]] = defaultdict(dict)

        # Build agent_image_configs by directly looking up configs
        for session in sessions:
            for kernel in session.kernels:
                agent_id = kernel.agent_id
                if agent_id:
                    # Image config must exist since we queried based on kernels
                    img_cfg = image_configs[kernel.image]

                    # Convert ImageConfigData to ImageConfig format
                    # Use canonical as key for agent_image_configs to avoid duplicates
                    canonical = img_cfg.canonical
                    if canonical not in agent_image_configs[agent_id]:
                        image_config = img_cfg.to_image_config(AutoPullBehavior(auto_pull))
                        agent_image_configs[agent_id][canonical] = image_config

        # Trigger image checking and pulling on each agent
        pull_tasks: list[Awaitable[Mapping[str, str]]] = []
        for agent_id, agent_images in agent_image_configs.items():
            agent_client = self._agent_pool.get_agent_client(agent_id)
            pull_tasks.append(agent_client.check_and_pull(agent_images))

        if pull_tasks:
            await asyncio.gather(*pull_tasks, return_exceptions=True)

    async def start_sessions(self) -> ScheduleResult:
        """
        Start sessions that have passed precondition checks.
        Transitions sessions from PREPARED to CREATING and starts kernels on agents.

        :return: ScheduleResult with the count of sessions started
        """
        # Get prepared sessions for starting
        sessions_with_images = await self._repository.get_sessions_for_start(
            [SessionStatus.PREPARED],
            [
                KernelStatus.PREPARED,
            ],
        )
        prepared_sessions = sessions_with_images.sessions
        image_configs = sessions_with_images.image_configs

        if not prepared_sessions:
            return ScheduleResult()
        # Extract session IDs for status update
        session_ids = [s.session_id for s in prepared_sessions]

        # Update sessions and kernels to CREATING status
        await self._repository.update_sessions_and_kernels_to_creating(session_ids)

        # Start sessions concurrently
        await self._start_sessions_concurrently(prepared_sessions, image_configs)

        # Convert prepared sessions to ScheduledSessionData format
        scheduled_data = [
            ScheduledSessionData(
                session_id=session.session_id,
                creation_id=session.creation_id,
                access_key=session.access_key,
                reason="triggered-by-scheduler",
            )
            for session in prepared_sessions
        ]
        return ScheduleResult(scheduled_sessions=scheduled_data)

    async def _start_sessions_concurrently(
        self,
        sessions: list[SessionDataForStart],
        image_configs: dict[str, ImageConfigData],
    ) -> None:
        """
        Start multiple sessions concurrently with individual timeouts.

        :param sessions: List of sessions to start
        :param image_configs: Image configurations for the sessions
        """

        async def start_with_timeout(session: SessionDataForStart) -> None:
            async with async_timeout.timeout(delay=START_SESSION_TIMEOUT_SEC):
                await self._start_single_session(session, image_configs)

        results = await asyncio.gather(
            *[start_with_timeout(session) for session in sessions],
            return_exceptions=True,
        )
        for session, result in zip(sessions, results, strict=True):
            if isinstance(result, BaseException):
                log.warning(
                    "start-session(s:{}): failed with unhandled exception",
                    session.session_id,
                    exc_info=result,
                )

    async def _start_single_session(
        self,
        session: SessionDataForStart,
        image_configs: dict[str, ImageConfigData],
    ) -> None:
        """
        Start a single session by creating kernels on agents.

        :param session: Session data to start
        :param image_configs: Image configurations for the session
        """
        log_fmt = "start-session(s:{}, type:{}, name:{}, ak:{}, cluster_mode:{}): "
        log_args = (
            session.session_id,
            session.session_type,
            session.name,
            session.access_key,
            session.cluster_mode,
        )
        log.debug(log_fmt + "try-starting", *log_args)

        try:
            # Ensure we have kernels to start
            if len(session.kernels) == 0:
                raise ValueError(f"Session {session.session_id} has no kernels")

            # Get resource policy and idle timeout
            # In production, this would come from database lookups
            idle_timeout = 600  # Default timeout in seconds
            if hasattr(self, "_repository") and hasattr(self._repository, "_db_source"):
                # Would need proper resource policy lookup
                pass

            # Setup network configuration
            network_setup = await self._setup_network_configuration(session)
            log.debug("ssh connection info mapping: {}", network_setup.cluster_ssh_port_mapping)

            # Setup environment variables - similar to registry.py
            # Group kernels by cluster role for replica counting
            keyfunc = lambda k: k.cluster_role
            replicas = {
                cluster_role: len(list(group_iterator))
                for cluster_role, group_iterator in groupby(
                    sorted(session.kernels, key=keyfunc),
                    key=keyfunc,
                )
            }
            environ: dict[str, str] = {
                **session.environ,
                "BACKENDAI_USER_UUID": str(session.user_uuid),
                "BACKENDAI_USER_EMAIL": session.user_email,
                "BACKENDAI_USER_NAME": session.user_name,
                "BACKENDAI_SESSION_ID": str(session.session_id),
                "BACKENDAI_SESSION_NAME": str(session.name),
                "BACKENDAI_CLUSTER_SIZE": str(len(session.kernels)),
                "BACKENDAI_CLUSTER_REPLICAS": ",".join(f"{k}:{v}" for k, v in replicas.items()),
                "BACKENDAI_CLUSTER_HOSTS": ",".join(
                    k.cluster_hostname or f"{k.cluster_role}{k.cluster_idx}"
                    for k in session.kernels
                ),
                "BACKENDAI_ACCESS_KEY": session.access_key,
                # BACKENDAI_SERVICE_PORTS are set as per-kernel env-vars.
                "BACKENDAI_PREOPEN_PORTS": (
                    ",".join(str(port) for port in session.kernels[0].preopen_ports)
                    if session.kernels and session.kernels[0].preopen_ports
                    else ""
                ),
            }

            # Group kernels by agent to minimize RPC calls
            kernels_by_agent: defaultdict[AgentId, list[KernelBindingData]] = defaultdict(list)
            for kernel in session.kernels:
                if kernel.agent_id:
                    kernels_by_agent[kernel.agent_id].append(kernel)

            # Create SSH keypair for cluster
            ssh_keypair = await self._create_cluster_ssh_keypair()

            # Convert ImageConfigData to ImageConfig format for agents
            image_configs_by_canonical: dict[str, ImageConfig] = {}
            for image_key, img_cfg in image_configs.items():
                image_config = img_cfg.to_image_config(AutoPullBehavior.DIGEST)
                image_configs_by_canonical[image_key] = image_config

            # Create kernels on each agent
            create_tasks: list[Awaitable[Any]] = []
            for agent_id, agent_kernels in kernels_by_agent.items():
                agent_client = self._agent_pool.get_agent_client(
                    agent_id, order_key=str(session.session_id)
                )

                # Prepare kernel creation configs
                kernel_ids = [str(k.kernel_id) for k in agent_kernels]
                kernel_configs: list[KernelCreationConfig] = []
                kernel_image_refs: dict[KernelId, ImageRef] = {}

                for idx, k in enumerate(agent_kernels):
                    kernel_id_str = str(k.kernel_id)
                    image_str = k.image

                    # Use resolved image config or fallback
                    if image_str not in image_configs_by_canonical:
                        # This should not happen - all images should be resolved by precondition check
                        log.error(
                            "Image {} not found in resolved configs - this indicates precondition check failed",
                            image_str,
                        )
                        raise ValueError(
                            f"Image {image_str} not found in database - session start failed"
                        )

                    kernel_image_config = image_configs_by_canonical[image_str]

                    # Use cluster configuration from kernel data
                    cluster_role = k.cluster_role
                    cluster_idx = k.cluster_idx
                    local_rank = k.local_rank
                    cluster_hostname = k.cluster_hostname or f"{cluster_role}{cluster_idx}"

                    # Build proper KernelCreationConfig matching registry.py format
                    kernel_config: KernelCreationConfig = {
                        "image": kernel_image_config,
                        "kernel_id": kernel_id_str,
                        "session_id": str(session.session_id),
                        "owner_user_id": str(session.user_uuid),
                        "owner_project_id": None,  # TODO: Implement project-owned sessions
                        "network_id": str(session.session_id),
                        "session_type": session.session_type,
                        "cluster_mode": session.cluster_mode,
                        "cluster_role": cluster_role,
                        "cluster_idx": cluster_idx,
                        "cluster_hostname": cluster_hostname,
                        "local_rank": local_rank,
                        "uid": k.uid,
                        "main_gid": k.main_gid,
                        "supplementary_gids": k.gids or [],
                        "resource_slots": k.requested_slots.to_json(),
                        "resource_opts": k.resource_opts or {},
                        "environ": {
                            **environ,
                            "BACKENDAI_KERNEL_ID": kernel_id_str,
                            "BACKENDAI_KERNEL_IMAGE": image_str,
                            "BACKENDAI_CLUSTER_ROLE": cluster_role,
                            "BACKENDAI_CLUSTER_IDX": str(cluster_idx),
                            "BACKENDAI_CLUSTER_LOCAL_RANK": str(local_rank),
                            "BACKENDAI_CLUSTER_HOST": cluster_hostname,
                            "BACKENDAI_SERVICE_PORTS": str(
                                kernel_image_config.get("labels", {}).get(
                                    "ai.backend.service-ports", ""
                                )
                            ),
                        },
                        "mounts": [
                            m.to_json() if hasattr(m, "to_json") else m for m in k.vfolder_mounts
                        ],
                        "package_directory": tuple(),
                        "idle_timeout": int(idle_timeout),
                        "bootstrap_script": k.bootstrap_script,
                        "startup_command": k.startup_command,
                        "internal_data": k.internal_data,
                        "auto_pull": kernel_image_config.get("auto_pull", AutoPullBehavior.DIGEST),
                        "preopen_ports": k.preopen_ports or [],
                        "allocated_host_ports": [],  # Will be populated by agent
                        "agent_addr": k.agent_addr or "",
                        "scaling_group": k.scaling_group,
                        "endpoint_id": None,  # For inference endpoints
                    }
                    kernel_configs.append(kernel_config)

                    # Create image ref for this kernel
                    kernel_image_refs[KernelId(k.kernel_id)] = ImageRef.from_image_str(
                        image_str,
                        project=kernel_image_config["project"],
                        registry=kernel_image_config["registry"]["name"],
                        architecture=k.architecture,
                        is_local=kernel_image_config["is_local"],
                    )

                # Create cluster info with network and SSH configuration
                cluster_info: ClusterInfo = {
                    "mode": session.cluster_mode,
                    "size": len(session.kernels),
                    "replicas": replicas,
                    "network_config": network_setup.network_config,
                    "ssh_keypair": ssh_keypair,
                    "cluster_ssh_port_mapping": network_setup.cluster_ssh_port_mapping,
                }

                # Create the kernels
                create_tasks.append(
                    agent_client.create_kernels(
                        str(session.session_id),
                        kernel_ids,
                        kernel_configs,
                        cluster_info,
                        kernel_image_refs,
                    )
                )

            if create_tasks:
                await asyncio.gather(*create_tasks, return_exceptions=True)

            log.info(log_fmt + "started", *log_args)

        except Exception as e:
            # Convert exception to error status info
            error_info = convert_to_status_data(e, self._config_provider.config.debug.enabled)
            log.warning(log_fmt + "failed-starting", *log_args, exc_info=True)
            # Update error info in status_data without changing status
            # Session will be retried by retry_creating_sessions later
            await self._repository.update_session_error_info(session.session_id, error_info)

    async def _setup_network_configuration(
        self,
        session: SessionDataForStart,
    ) -> NetworkSetup:
        """
        Setup network configuration based on session network type.

        :param session: Session data containing network type and configuration
        :return: NetworkSetup with network config and SSH port mapping
        """
        network_name: Optional[str] = None
        network_config: dict[str, Any] = {}
        cluster_ssh_port_mapping: Optional[ClusterSSHPortMapping] = None

        network_type = session.network_type or NetworkType.VOLATILE

        if network_type == NetworkType.PERSISTENT:
            # For persistent networks, use pre-created network
            if session.network_id:
                # In production, would look up network details from database
                network_name = f"persistent-{session.network_id}"
                network_config = {"mode": "bridge", "network_name": network_name}
        elif network_type == NetworkType.VOLATILE:
            if session.cluster_mode == ClusterMode.SINGLE_NODE and len(session.kernels) > 1:
                # Create single-node network for multi-kernel sessions
                network_name = f"bai-singlenode-{session.session_id}"
                first_kernel = session.kernels[0]
                if not first_kernel.agent_id:
                    raise ValueError(f"No agent assigned for kernel {first_kernel.kernel_id}")
                agent_client = self._agent_pool.get_agent_client(
                    first_kernel.agent_id, order_key=str(session.session_id)
                )
                try:
                    await agent_client.create_local_network(network_name)
                except Exception:
                    log.exception(f"Failed to create agent-local network {network_name}")
                    raise
                network_config = {
                    "mode": "bridge",
                    "network_name": network_name,
                }
            elif session.cluster_mode == ClusterMode.MULTI_NODE:
                # Create overlay network for multi-node sessions
                driver = self._config_provider.config.network.inter_container.default_driver
                if driver is None:
                    raise ValueError("No inter-container network driver is configured.")

                # Check if plugin is available
                if driver not in self._network_plugin_ctx.plugins:
                    available_plugins = list(self._network_plugin_ctx.plugins.keys())
                    log.error(
                        f"Network plugin '{driver}' not found. Available plugins: {available_plugins}. "
                        f"For overlay networks, ensure Docker Swarm is initialized with 'docker swarm init'."
                    )
                    raise KeyError(
                        f"Network plugin '{driver}' not found. Available plugins: {available_plugins}. "
                        f"For overlay networks, ensure Docker Swarm is initialized with 'docker swarm init'."
                    )

                network_plugin = self._network_plugin_ctx.plugins[driver]
                try:
                    network_info = await network_plugin.create_network(
                        identifier=str(session.session_id)
                    )
                    network_config = dict(network_info.options)
                    network_name = network_info.network_id
                except Exception:
                    log.exception(
                        f"Failed to create the inter-container network (plugin: {driver})"
                    )
                    raise
        elif network_type == NetworkType.HOST:
            network_config = {"mode": "host"}
            network_name = "host"

            # Setup SSH port mapping for multi-kernel sessions in host mode
            if len(session.kernels) > 1:
                port_mapping: dict[str, tuple[str, int]] = {}
                for kernel in session.kernels:
                    if not kernel.agent_id:
                        log.warning(
                            f"No agent assigned for kernel {kernel.kernel_id}, skipping port mapping"
                        )
                        continue
                    agent_client = self._agent_pool.get_agent_client(
                        kernel.agent_id, order_key=str(session.session_id)
                    )
                    port = await agent_client.assign_port()
                    # Extract host from agent_addr
                    agent_addr = kernel.agent_addr or ""
                    agent_host = (
                        agent_addr.replace("tcp://", "").split(":", maxsplit=1)[0]
                        if agent_addr
                        else "localhost"
                    )
                    cluster_hostname = f"node-{kernel.kernel_id}"
                    port_mapping[cluster_hostname] = (agent_host, port)
                cluster_ssh_port_mapping = ClusterSSHPortMapping(port_mapping)

        await self._repository.update_session_network_id(
            session.session_id,
            network_name,
        )
        return NetworkSetup(
            network_name=network_name,
            network_config=network_config,
            cluster_ssh_port_mapping=cluster_ssh_port_mapping,
        )

    async def _create_cluster_ssh_keypair(self) -> ClusterSSHKeyPair:
        """
        Create SSH keypair for cluster communication.
        Generates actual RSA SSH keys using cryptography library.

        :return: ClusterSSHKeyPair with 'public_key' and 'private_key'
        """
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
        return ClusterSSHKeyPair(
            private_key=pem.decode("utf-8"),
            public_key=public_key.decode("utf-8"),
        )

    def _filter_stuck_sessions_for_pull(
        self,
        sessions: list[SessionDataForPull],
        threshold: float,
    ) -> list[SessionDataForPull]:
        """
        Filter sessions that appear stuck based on kernel status change time.

        :param sessions: List of sessions to filter
        :param threshold: Time threshold in seconds
        :return: List of stuck sessions
        """
        current_time = time.time()
        stuck_sessions: list[SessionDataForPull] = []

        for session in sessions:
            # Check the oldest kernel's status_changed time
            oldest_status_change = min(
                (kernel.status_changed for kernel in session.kernels if kernel.status_changed),
                default=None,
            )

            if oldest_status_change is None:
                # No status change info, consider it stuck
                stuck_sessions.append(session)
            elif (current_time - oldest_status_change) >= threshold:
                # Status hasn't changed for too long
                stuck_sessions.append(session)

        return stuck_sessions

    async def _check_truly_stuck_pulling_sessions(
        self,
        sessions: list[SessionDataForPull],
        image_configs: dict[str, ImageConfigData],
    ) -> list[SessionDataForPull]:
        """
        Check if sessions are truly stuck by verifying if pulling is still in progress.

        :param sessions: List of potentially stuck sessions
        :param image_configs: Image configurations
        :return: List of sessions that are truly stuck
        """
        truly_stuck_sessions: list[SessionDataForPull] = []

        # Group images by agent to check pulling status
        agent_images: defaultdict[AgentId, set[str]] = defaultdict(set)
        session_images: dict[SessionId, set[str]] = {}

        for session in sessions:
            session_image_set = set()
            for kernel in session.kernels:
                if kernel.agent_id and kernel.image in image_configs:
                    img_cfg = image_configs[kernel.image]
                    canonical = img_cfg.canonical
                    agent_images[kernel.agent_id].add(canonical)
                    session_image_set.add(canonical)
            session_images[session.session_id] = session_image_set

        # Check pulling status for each agent
        agent_pulling_status: dict[AgentId, dict[str, bool]] = {}
        for agent_id, images in agent_images.items():
            agent_client = self._agent_pool.get_agent_client(agent_id)
            pulling_status = {}
            for image in images:
                try:
                    is_pulling = await agent_client.check_pulling(image)
                    pulling_status[image] = is_pulling
                except Exception as e:
                    log.warning(
                        "Failed to check pulling status for image {} on agent {}: {}",
                        image,
                        agent_id,
                        e,
                    )
                    # If we can't check, assume it's stuck
                    pulling_status[image] = False
            agent_pulling_status[agent_id] = pulling_status

        # Determine truly stuck sessions
        for session in sessions:
            images_to_check = session_images[session.session_id]
            if not images_to_check:
                # No images to check, consider it stuck
                truly_stuck_sessions.append(session)
                continue

            # Check if any image for this session is actively being pulled
            any_pulling = False
            for kernel in session.kernels:
                if kernel.agent_id and kernel.image in image_configs:
                    img_cfg = image_configs[kernel.image]
                    canonical = img_cfg.canonical
                    if agent_pulling_status.get(kernel.agent_id, {}).get(canonical, False):
                        any_pulling = True
                        break

            if not any_pulling:
                # No images are being pulled, session is truly stuck
                truly_stuck_sessions.append(session)

        return truly_stuck_sessions

    async def retry_preparing_sessions(self) -> ScheduleResult:
        """
        Retry PREPARING/PULLING sessions that appear stuck.
        Re-triggers check_and_pull operations for their images.

        :return: ScheduleResult with number of sessions retried
        """
        PREPARING_CHECK_THRESHOLD = 10.0  # 10 seconds

        # Get sessions with PREPARING and PULLING statuses
        sessions_with_images = await self._repository.get_sessions_for_pull(
            [
                SessionStatus.PREPARING,
                SessionStatus.PULLING,
            ],
            [
                KernelStatus.SCHEDULED,
                KernelStatus.PREPARING,
                KernelStatus.PULLING,
            ],
        )
        sessions = sessions_with_images.sessions
        image_configs = sessions_with_images.image_configs

        if not sessions:
            log.trace("No sessions found with PREPARING/PULLING status")
            return ScheduleResult()

        # Filter sessions that haven't changed status for threshold time
        stuck_sessions = self._filter_stuck_sessions_for_pull(sessions, PREPARING_CHECK_THRESHOLD)

        if not stuck_sessions:
            return ScheduleResult()

        # Check which sessions are actually stuck (not actively pulling)
        truly_stuck_sessions = await self._check_truly_stuck_pulling_sessions(
            stuck_sessions, image_configs
        )

        if not truly_stuck_sessions:
            log.debug("All sessions are actively pulling, no retry needed")
            return ScheduleResult()

        log.info("Retrying {} truly stuck PREPARING/PULLING sessions", len(truly_stuck_sessions))

        # Update retry counts and get sessions that should continue retrying
        stuck_session_ids = [session.session_id for session in truly_stuck_sessions]
        sessions_to_retry_ids = await self._repository.batch_update_stuck_session_retries(
            stuck_session_ids, SERVICE_MAX_RETRIES
        )

        if not sessions_to_retry_ids:
            log.info("All stuck sessions exceeded max retries, moved to PENDING")
            return ScheduleResult()

        # Filter sessions that should be retried based on returned IDs
        sessions_to_retry = [
            session
            for session in truly_stuck_sessions
            if session.session_id in sessions_to_retry_ids
        ]

        # Use the existing _trigger_image_pulling_for_sessions method
        await self._trigger_image_pulling_for_sessions(sessions_to_retry, image_configs)

        # Convert retried sessions to ScheduledSessionData format
        scheduled_data = [
            ScheduledSessionData(
                session_id=session.session_id,
                creation_id=session.creation_id,
                access_key=session.access_key,
                reason="triggered-by-scheduler",
            )
            for session in sessions_to_retry
        ]
        return ScheduleResult(scheduled_sessions=scheduled_data)

    def _filter_stuck_sessions_for_start(
        self,
        sessions: list[SessionDataForStart],
        threshold: float,
    ) -> list[SessionDataForStart]:
        """
        Filter sessions that appear stuck based on kernel status change time.

        :param sessions: List of sessions to filter
        :param threshold: Time threshold in seconds
        :return: List of stuck sessions
        """
        current_time = time.time()
        stuck_sessions: list[SessionDataForStart] = []

        for session in sessions:
            # Check the oldest kernel's status_changed time
            oldest_status_change = min(
                (kernel.status_changed for kernel in session.kernels if kernel.status_changed),
                default=None,
            )

            if oldest_status_change is None:
                # No status change info, consider it stuck
                stuck_sessions.append(session)
            elif (current_time - oldest_status_change) >= threshold:
                # Status hasn't changed for too long
                stuck_sessions.append(session)

        return stuck_sessions

    async def _check_truly_stuck_creating_sessions(
        self,
        sessions: list[SessionDataForStart],
    ) -> list[SessionDataForStart]:
        """
        Check if sessions are truly stuck by verifying if kernels are being created or already exist.

        :param sessions: List of potentially stuck sessions
        :return: List of sessions that are truly stuck
        """
        truly_stuck_sessions: list[SessionDataForStart] = []

        for session in sessions:
            # Check each kernel in the session
            any_active = False
            for kernel in session.kernels:
                if kernel.agent_id:
                    agent_client = self._agent_pool.get_agent_client(kernel.agent_id)
                    try:
                        # Check if kernel is being created or already exists
                        is_active = await agent_client.check_creating(str(kernel.kernel_id))
                        if is_active:
                            any_active = True
                            break
                    except Exception as e:
                        log.warning(
                            "Failed to check creating status for kernel {} on agent {}: {}",
                            kernel.kernel_id,
                            kernel.agent_id,
                            e,
                        )
                        # If we can't check, assume it's stuck

            if not any_active:
                # No kernels are being created or existing, session is truly stuck
                truly_stuck_sessions.append(session)

        return truly_stuck_sessions

    async def retry_creating_sessions(self) -> ScheduleResult:
        """
        Retry CREATING sessions that appear stuck.
        Re-triggers kernel creation operations directly.

        :return: ScheduleResult with number of sessions retried
        """
        CREATING_CHECK_THRESHOLD = 10.0  # 10 seconds

        # Get CREATING sessions from repository
        sessions_with_images = await self._repository.get_sessions_for_start(
            [SessionStatus.CREATING],
            [
                KernelStatus.PREPARED,
                KernelStatus.CREATING,
            ],
        )
        sessions = sessions_with_images.sessions
        image_configs = sessions_with_images.image_configs

        if not sessions:
            return ScheduleResult()

        # Filter sessions that haven't changed status for threshold time
        stuck_sessions = self._filter_stuck_sessions_for_start(sessions, CREATING_CHECK_THRESHOLD)

        if not stuck_sessions:
            return ScheduleResult()

        # Check which sessions are truly stuck (not actively creating)
        truly_stuck_sessions = await self._check_truly_stuck_creating_sessions(stuck_sessions)

        if not truly_stuck_sessions:
            log.debug("All sessions are actively creating kernels, no retry needed")
            return ScheduleResult()

        log.info("Retrying {} truly stuck CREATING sessions", len(truly_stuck_sessions))

        # Update retry counts and get sessions that should continue retrying
        stuck_session_ids = [session.session_id for session in truly_stuck_sessions]
        sessions_to_retry_ids = await self._repository.batch_update_stuck_session_retries(
            stuck_session_ids, SERVICE_MAX_RETRIES
        )

        if not sessions_to_retry_ids:
            log.info("All stuck sessions exceeded max retries, moved to PENDING")
            return ScheduleResult()

        # Filter sessions that should be retried based on returned IDs
        sessions_to_retry = [
            session
            for session in truly_stuck_sessions
            if session.session_id in sessions_to_retry_ids
        ]

        # Use the existing _start_sessions_concurrently method to retry
        # This will re-trigger kernel creation for stuck sessions
        await self._start_sessions_concurrently(sessions_to_retry, image_configs)

        # Convert retried sessions to ScheduledSessionData format
        scheduled_data = [
            ScheduledSessionData(
                session_id=session.session_id,
                creation_id=session.creation_id,
                access_key=session.access_key,
                reason="triggered-by-scheduler",
            )
            for session in sessions_to_retry
        ]
        return ScheduleResult(scheduled_sessions=scheduled_data)
