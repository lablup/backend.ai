from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from collections.abc import Awaitable, Mapping
from dataclasses import dataclass
from itertools import groupby
from typing import Any, Optional

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
from ai.backend.manager.clients.agent import AgentClientPool
from ai.backend.manager.config.provider import ManagerConfigProvider
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
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.types import (
    ImageConfigData,
    KernelBindingData,
    NetworkSetup,
    RetryResult,
    SessionDataForPull,
    SessionDataForStart,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@dataclass
class SessionLauncherArgs:
    repository: SchedulerRepository
    agent_client_pool: AgentClientPool
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
    _agent_client_pool: AgentClientPool
    _network_plugin_ctx: NetworkPluginContext
    _config_provider: ManagerConfigProvider
    _valkey_schedule: ValkeyScheduleClient
    _phase_metrics: SchedulerPhaseMetricObserver

    def __init__(self, args: SessionLauncherArgs) -> None:
        self._repository = args.repository
        self._agent_client_pool = args.agent_client_pool
        self._network_plugin_ctx = args.network_plugin_ctx
        self._config_provider = args.config_provider
        self._valkey_schedule = args.valkey_schedule
        self._phase_metrics = SchedulerPhaseMetricObserver.instance()

    async def trigger_image_pulling(
        self,
        sessions: list[SessionDataForPull],
        image_configs: dict[str, ImageConfigData],
    ) -> None:
        """
        Trigger image checking and pulling on agents for the given sessions.

        Public method for SessionLifecycleHandler pattern.
        Used by CheckPreconditionLifecycleHandler to trigger image pulling
        after coordinator queries sessions.

        :param sessions: List of sessions with kernels
        :param image_configs: Image configurations indexed by image name
        """
        await self._trigger_image_pulling_for_sessions(sessions, image_configs)

    async def _trigger_image_pulling_for_sessions(
        self,
        sessions: list[SessionDataForPull],
        image_configs: dict[str, ImageConfigData],
    ) -> None:
        """
        Trigger image checking and pulling on agents for the given sessions.

        Internal implementation method.

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
        async def pull_for_agent(
            agent_id: AgentId, images: dict[str, ImageConfig]
        ) -> Mapping[str, str]:
            async with self._agent_client_pool.acquire(agent_id) as client:
                return await client.check_and_pull(images)

        pull_tasks: list[Awaitable[Mapping[str, str]]] = []
        for agent_id, agent_images in agent_image_configs.items():
            pull_tasks.append(pull_for_agent(agent_id, agent_images))

        if pull_tasks:
            with RecorderContext[SessionId].shared_phase(
                "prepare_images",
                success_detail="Image pull requested",
            ):
                with RecorderContext[SessionId].shared_step(
                    "check_and_pull_images",
                    success_detail="Image pull triggered",
                ):
                    await asyncio.gather(*pull_tasks, return_exceptions=True)

    async def start_sessions_for_handler(
        self,
        sessions: list[SessionDataForStart],
        image_configs: dict[str, ImageConfigData],
    ) -> None:
        """
        Start sessions on agents for the given sessions.

        Public method for SessionLifecycleHandler pattern.
        Used by StartSessionsLifecycleHandler to start sessions
        after coordinator queries sessions with user data.

        Note: Status transition is handled by the Coordinator, not here.

        :param sessions: List of sessions with full data for starting
        :param image_configs: Image configurations indexed by image name
        """
        with RecorderContext[SessionId].shared_phase(
            "trigger_kernel_creation",
            success_detail="Kernel creation triggered",
        ):
            with RecorderContext[SessionId].shared_step(
                "create_kernels",
                success_detail="Kernel creation requested",
            ):
                await self._start_sessions_concurrently(sessions, image_configs)

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
            async def create_kernels_on_agent(
                agent_id: AgentId,
                agent_kernels: list[KernelBindingData],
            ) -> None:
                # Prepare kernel creation configs
                kernel_ids = [k.kernel_id for k in agent_kernels]
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

                # Create the kernels using connection pool
                async with self._agent_client_pool.acquire(agent_id) as client:
                    await client.create_kernels(
                        session.session_id,
                        kernel_ids,
                        kernel_configs,
                        cluster_info,
                        kernel_image_refs,
                    )

            create_tasks: list[Awaitable[None]] = []
            for agent_id, agent_kernels in kernels_by_agent.items():
                create_tasks.append(create_kernels_on_agent(agent_id, agent_kernels))

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
                try:
                    async with self._agent_client_pool.acquire(first_kernel.agent_id) as client:
                        await client.create_local_network(network_name)
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
                    async with self._agent_client_pool.acquire(kernel.agent_id) as client:
                        port = await client.assign_port()
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

        # Check pulling status for each agent in parallel
        check_tasks = [
            self._check_agent_pulling_status(agent_id, images)
            for agent_id, images in agent_images.items()
        ]
        results = await asyncio.gather(*check_tasks, return_exceptions=True)

        agent_pulling_status: dict[AgentId, dict[str, bool]] = {}
        for result in results:
            if isinstance(result, BaseException):
                log.warning("Failed to check pulling status: {}", result)
                continue
            agent_id, pulling_status = result
            agent_pulling_status[agent_id] = pulling_status

        # Determine truly stuck sessions
        pool = RecorderContext[SessionId].current_pool()
        for session in sessions:
            recorder = pool.recorder(session.session_id)
            with recorder.phase(
                "verify_pull_status",
                success_detail="Image pull status verified",
            ):
                with recorder.step(
                    "check_pull_progress",
                    success_detail="Image pull progress checked",
                ):
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

    async def _check_agent_pulling_status(
        self,
        agent_id: AgentId,
        images: set[str],
    ) -> tuple[AgentId, dict[str, bool]]:
        """Check pulling status for all images on a single agent."""
        pulling_status: dict[str, bool] = {}
        try:
            async with self._agent_client_pool.acquire(agent_id) as client:
                for image in images:
                    try:
                        is_pulling = await client.check_pulling(image)
                        pulling_status[image] = is_pulling
                    except Exception as e:
                        log.warning(
                            "Failed to check pulling status for image {} on agent {}: {}",
                            image,
                            agent_id,
                            e,
                        )
                        pulling_status[image] = False
        except Exception as e:
            log.warning(
                "Failed to acquire connection for agent {}: {}",
                agent_id,
                e,
            )
            for image in images:
                pulling_status[image] = False
        return agent_id, pulling_status

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
        if not sessions:
            return []

        # Check all sessions in parallel
        check_tasks = [self._check_session_has_active_kernels(session) for session in sessions]
        results = await asyncio.gather(*check_tasks, return_exceptions=True)

        # Filter sessions that have no active kernels
        truly_stuck_sessions: list[SessionDataForStart] = []
        pool = RecorderContext[SessionId].current_pool()
        for session, result in zip(sessions, results, strict=True):
            recorder = pool.recorder(session.session_id)
            with recorder.phase(
                "verify_creation_status",
                success_detail="Kernel creation status verified",
            ):
                with recorder.step(
                    "check_kernel_status",
                    success_detail="Kernel creation status checked",
                ):
                    if isinstance(result, BaseException):
                        log.warning(
                            "Failed to check session {} creating status: {}",
                            session.session_id,
                            result,
                        )
                        # If we can't check, assume it's stuck
                        truly_stuck_sessions.append(session)
                    elif not result:
                        # No active kernels, session is stuck
                        truly_stuck_sessions.append(session)

        return truly_stuck_sessions

    async def _check_session_has_active_kernels(
        self,
        session: SessionDataForStart,
    ) -> bool:
        """Check if any kernel in the session is being created or already exists."""
        for kernel in session.kernels:
            if not kernel.agent_id:
                continue
            try:
                async with self._agent_client_pool.acquire(kernel.agent_id) as client:
                    is_active = await client.check_creating(kernel.kernel_id)
                    if is_active:
                        return True
            except Exception as e:
                log.warning(
                    "Failed to check creating status for kernel {} on agent {}: {}",
                    kernel.kernel_id,
                    kernel.agent_id,
                    e,
                )
        return False

    async def retry_preparing_for_handler(
        self,
        sessions: list[SessionDataForPull],
        image_configs: dict[str, ImageConfigData],
    ) -> RetryResult:
        """
        Retry PREPARING/PULLING sessions for the given sessions list.

        Handler-specific method that works with pre-fetched data.
        Used by RetryPreparingLifecycleHandler.

        :param sessions: List of sessions to check for retry
        :param image_configs: Image configurations indexed by image name
        :return: RetryResult with retried_ids and exceeded_ids for Coordinator to process
        """
        PREPARING_CHECK_THRESHOLD = 10.0  # 10 seconds

        empty_result = RetryResult(retried_ids=[], exceeded_ids=[])

        if not sessions:
            return empty_result

        # Filter sessions that haven't changed status for threshold time
        stuck_sessions = self._filter_stuck_sessions_for_pull(sessions, PREPARING_CHECK_THRESHOLD)

        if not stuck_sessions:
            return empty_result

        # Check which sessions are actually stuck (not actively pulling)
        truly_stuck_sessions = await self._check_truly_stuck_pulling_sessions(
            stuck_sessions, image_configs
        )

        if not truly_stuck_sessions:
            log.debug("All sessions are actively pulling, no retry needed")
            return empty_result

        log.info("Retrying {} truly stuck PREPARING/PULLING sessions", len(truly_stuck_sessions))

        # Update retry counts and get sessions that should continue retrying
        stuck_session_ids = [session.session_id for session in truly_stuck_sessions]
        retry_update_result = await self._repository.batch_update_stuck_session_retries(
            stuck_session_ids, SERVICE_MAX_RETRIES
        )

        if not retry_update_result.sessions_to_retry:
            log.info("All stuck sessions exceeded max retries")
            return RetryResult(retried_ids=[], exceeded_ids=retry_update_result.sessions_exceeded)

        # Filter sessions that should be retried based on returned IDs
        sessions_to_retry = [
            session
            for session in truly_stuck_sessions
            if session.session_id in retry_update_result.sessions_to_retry
        ]

        # Use the existing _trigger_image_pulling_for_sessions method
        with RecorderContext[SessionId].shared_phase(
            "prepare_images",
            success_detail="Image pull retried",
        ):
            with RecorderContext[SessionId].shared_step(
                "retry_image_pulling",
                success_detail="Image pull retried",
            ):
                await self._trigger_image_pulling_for_sessions(sessions_to_retry, image_configs)

        return RetryResult(
            retried_ids=list(retry_update_result.sessions_to_retry),
            exceeded_ids=list(retry_update_result.sessions_exceeded),
        )

    async def retry_creating_for_handler(
        self,
        sessions: list[SessionDataForStart],
        image_configs: dict[str, ImageConfigData],
    ) -> RetryResult:
        """
        Retry CREATING sessions for the given sessions list.

        Handler-specific method that works with pre-fetched data.
        Used by RetryCreatingLifecycleHandler.

        :param sessions: List of sessions to check for retry
        :param image_configs: Image configurations indexed by image name
        :return: RetryResult with retried_ids and exceeded_ids for Coordinator to process
        """
        CREATING_CHECK_THRESHOLD = 10.0  # 10 seconds

        empty_result = RetryResult(retried_ids=[], exceeded_ids=[])

        if not sessions:
            return empty_result

        # Filter sessions that haven't changed status for threshold time
        stuck_sessions = self._filter_stuck_sessions_for_start(sessions, CREATING_CHECK_THRESHOLD)

        if not stuck_sessions:
            return empty_result

        # Check which sessions are truly stuck (not actively creating)
        truly_stuck_sessions = await self._check_truly_stuck_creating_sessions(stuck_sessions)

        if not truly_stuck_sessions:
            log.debug("All sessions are actively creating kernels, no retry needed")
            return empty_result

        log.info("Retrying {} truly stuck CREATING sessions", len(truly_stuck_sessions))

        # Update retry counts and get sessions that should continue retrying
        stuck_session_ids = [session.session_id for session in truly_stuck_sessions]
        retry_update_result = await self._repository.batch_update_stuck_session_retries(
            stuck_session_ids, SERVICE_MAX_RETRIES
        )

        if not retry_update_result.sessions_to_retry:
            log.info("All stuck sessions exceeded max retries")
            return RetryResult(retried_ids=[], exceeded_ids=retry_update_result.sessions_exceeded)

        # Filter sessions that should be retried based on returned IDs
        sessions_to_retry = [
            session
            for session in truly_stuck_sessions
            if session.session_id in retry_update_result.sessions_to_retry
        ]

        # Use the existing _start_sessions_concurrently method to retry
        await self._start_sessions_concurrently(sessions_to_retry, image_configs)

        return RetryResult(
            retried_ids=list(retry_update_result.sessions_to_retry),
            exceeded_ids=list(retry_update_result.sessions_exceeded),
        )
