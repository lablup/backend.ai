from __future__ import annotations

import logging
from contextlib import asynccontextmanager as actxmgr
from typing import Any, AsyncIterator, Mapping, Optional

from ai.backend.common.docker import ImageRef
from ai.backend.common.exception import BackendAIError
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.policies.retry import BackoffStrategy, RetryArgs, RetryPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import (
    AgentId,
    ClusterInfo,
    ImageConfig,
    KernelCreationConfig,
    KernelId,
)
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.agent_cache import AgentRPCCache, PeerInvoker

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

agent_client_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)),
        RetryPolicy(
            RetryArgs(
                max_retries=3,
                retry_delay=0.1,
                backoff_strategy=BackoffStrategy.EXPONENTIAL,
                non_retryable_exceptions=(BackendAIError,),
            )
        ),
    ]
)


class AgentClient:
    """
    Client for communicating with a single agent via RPC.
    Wraps all RPC calls to the agent to provide a cleaner interface.
    """

    _agent_cache: AgentRPCCache
    _agent_id: AgentId
    _invoke_timeout: Optional[float]
    _order_key: Optional[str]

    def __init__(
        self,
        agent_cache: AgentRPCCache,
        agent_id: AgentId,
        *,
        invoke_timeout: Optional[float] = None,
        order_key: Optional[str] = None,
    ) -> None:
        self._agent_cache = agent_cache
        self._agent_id = agent_id
        self._invoke_timeout = invoke_timeout
        self._order_key = order_key

    @property
    def agent_id(self) -> AgentId:
        return self._agent_id

    @actxmgr
    async def _with_connection(self) -> AsyncIterator[PeerInvoker]:
        """
        Context manager to get a PeerInvoker for the agent.
        This will automatically handle connection management.
        """
        async with self._agent_cache.rpc_context(
            self._agent_id,
            invoke_timeout=self._invoke_timeout,
            order_key=self._order_key,
        ) as rpc:
            yield rpc

    # Hardware information methods
    @agent_client_resilience.apply()
    async def health(self) -> Mapping[str, Any]:
        """Get lightweight health information from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.health()

    @agent_client_resilience.apply()
    async def gather_hwinfo(self) -> Mapping[str, Any]:
        """Gather hardware information from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.gather_hwinfo(agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def scan_gpu_alloc_map(self) -> Mapping[str, Any]:
        """Scan GPU allocation map from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.scan_gpu_alloc_map(agent_id=self.agent_id)

    # Image management methods
    @agent_client_resilience.apply()
    async def check_and_pull(self, image_configs: Mapping[str, ImageConfig]) -> Mapping[str, str]:
        """Check and pull images on the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.check_and_pull(image_configs, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def purge_images(
        self,
        images: list[str],
        force: bool,
        noprune: bool,
    ) -> Mapping[str, Any]:
        """Purge images from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.purge_images(images, force, noprune, agent_id=self.agent_id)

    # Network management methods
    @agent_client_resilience.apply()
    async def create_local_network(self, network_name: str) -> None:
        """Create a local network on the agent."""
        async with self._with_connection() as rpc:
            await rpc.call.create_local_network(network_name, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def destroy_local_network(self, network_ref_name: str) -> None:
        """Destroy a local network on the agent."""
        async with self._with_connection() as rpc:
            await rpc.call.destroy_local_network(network_ref_name, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def assign_port(self) -> int:
        """Assign a host port on the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.assign_port(agent_id=self.agent_id)

    # Kernel management methods
    @agent_client_resilience.apply()
    async def create_kernels(
        self,
        session_id: str,
        kernel_ids: list[str],
        kernel_configs: list[KernelCreationConfig],
        cluster_info: ClusterInfo,
        kernel_image_refs: Mapping[KernelId, ImageRef],
    ) -> Any:
        """Create kernels on the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.create_kernels(
                session_id,
                kernel_ids,
                kernel_configs,
                cluster_info,
                kernel_image_refs,
                agent_id=self.agent_id,
            )

    @agent_client_resilience.apply()
    async def destroy_kernel(
        self,
        kernel_id: str,
        session_id: str,
        reason: str,
        suppress_events: bool = True,
    ) -> None:
        """Destroy a kernel on the agent."""
        async with self._with_connection() as rpc:
            await rpc.call.destroy_kernel(
                kernel_id,
                session_id,
                reason,
                suppress_events=suppress_events,
                agent_id=self.agent_id,
            )

    @agent_client_resilience.apply()
    async def restart_kernel(
        self,
        session_id: str,
        kernel_id: str,
        image_ref: Any,
        update_config: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Restart a kernel on the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.restart_kernel(
                session_id,
                kernel_id,
                image_ref,
                update_config,
                agent_id=self.agent_id,
            )

    @agent_client_resilience.apply()
    async def sync_kernel_registry(self, kernel_tuples: list[tuple[str, str]]) -> None:
        """Sync kernel registry on the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.sync_kernel_registry(kernel_tuples, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def drop_kernel_registry(self, kernel_id_list: list[KernelId]) -> None:
        """Drop kernel registry entries on the agent."""
        async with self._with_connection() as rpc:
            await rpc.call.drop_kernel_registry(kernel_id_list, agent_id=self.agent_id)

    # Health monitoring methods
    @agent_client_resilience.apply()
    async def check_pulling(self, image_name: str) -> bool:
        """Check if an image is being pulled."""
        async with self._with_connection() as rpc:
            return await rpc.call.check_pulling(image_name, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def check_creating(self, kernel_id: str) -> bool:
        """Check if a kernel is being created."""
        async with self._with_connection() as rpc:
            return await rpc.call.check_creating(str(kernel_id), agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def check_running(self, kernel_id: str) -> bool:
        """Check if a kernel is running."""
        async with self._with_connection() as rpc:
            return await rpc.call.check_running(str(kernel_id), agent_id=self.agent_id)

    # Container management methods
    @agent_client_resilience.apply()
    async def purge_containers(self, serialized_data: list[tuple[str, str]]) -> None:
        """Purge containers on the agent."""
        async with self._with_connection() as rpc:
            await rpc.call.purge_containers(serialized_data, agent_id=self.agent_id)

    # Code execution methods
    @agent_client_resilience.apply()
    async def execute(
        self,
        session_id: str,
        kernel_id: str,
        major_api_version: int,
        run_id: str,
        mode: str,
        code: str,
        opts: Mapping[str, Any],
        flush_timeout: float | None,
    ) -> Mapping[str, Any]:
        """Execute code on the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.execute(
                session_id,
                kernel_id,
                major_api_version,
                run_id,
                mode,
                code,
                opts,
                flush_timeout,
                agent_id=self.agent_id,
            )

    @agent_client_resilience.apply()
    async def interrupt_kernel(self, kernel_id: str) -> Mapping[str, Any]:
        """Interrupt a kernel on the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.interrupt_kernel(kernel_id, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def trigger_batch_execution(
        self,
        session_id: str,
        kernel_id: str,
        startup_command: str,
        batch_timeout: float,
    ) -> None:
        """Trigger batch execution on the agent."""
        async with self._with_connection() as rpc:
            await rpc.call.trigger_batch_execution(
                session_id,
                kernel_id,
                startup_command,
                batch_timeout,
                agent_id=self.agent_id,
            )

    @agent_client_resilience.apply()
    async def get_completions(
        self,
        kernel_id: str,
        text: str,
        opts: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Get code completions from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.get_completions(kernel_id, text, opts, agent_id=self.agent_id)

    # Service management methods
    @agent_client_resilience.apply()
    async def start_service(
        self,
        kernel_id: str,
        service: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Start a service on the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.start_service(kernel_id, service, opts, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def shutdown_service(self, kernel_id: str, service: str) -> None:
        """Shutdown a service on the agent."""
        async with self._with_connection() as rpc:
            await rpc.call.shutdown_service(kernel_id, service, agent_id=self.agent_id)

    # File management methods
    @agent_client_resilience.apply()
    async def upload_file(self, kernel_id: str, filename: str, payload: bytes) -> Mapping[str, Any]:
        """Upload a file to the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.upload_file(kernel_id, filename, payload, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def download_file(self, kernel_id: str, filepath: str) -> bytes:
        """Download a file from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.download_file(kernel_id, filepath, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def download_single(self, kernel_id: str, filepath: str) -> bytes:
        """Download a single file from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.download_single(kernel_id, filepath, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def list_files(self, kernel_id: str, path: str) -> Mapping[str, Any]:
        """List files on the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.list_files(kernel_id, path, agent_id=self.agent_id)

    # Log management methods
    @agent_client_resilience.apply()
    async def get_logs(self, kernel_id: str) -> Mapping[str, str]:
        """Get logs from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.get_logs(kernel_id, agent_id=self.agent_id)

    # Image commit methods
    @agent_client_resilience.apply()
    async def commit(
        self,
        kernel_id: str,
        email: str,
        canonical: Optional[str] = None,
        extra_labels: Optional[dict[str, str]] = None,
        filename: Optional[str] = None,
    ) -> Mapping[str, Any]:
        """Commit a kernel image on the agent."""
        async with self._with_connection() as rpc:
            kwargs: dict[str, Any] = {}
            if canonical is not None:
                kwargs["canonical"] = canonical
            if extra_labels is not None:
                kwargs["extra_labels"] = extra_labels
            if filename is not None:
                kwargs["filename"] = filename
            kwargs["agent_id"] = self.agent_id

            return await rpc.call.commit(kernel_id, email, **kwargs)

    @agent_client_resilience.apply()
    async def push_image(self, image_ref: ImageRef, registry: Any) -> Mapping[str, Any]:
        """Push an image from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.push_image(image_ref, registry, agent_id=self.agent_id)

    # Scaling group management
    @agent_client_resilience.apply()
    async def update_scaling_group(self, scaling_group: str) -> None:
        """Update scaling group on the agent."""
        async with self._with_connection() as rpc:
            await rpc.call.update_scaling_group(scaling_group, self.agent_id)

    # Local configuration management
    @agent_client_resilience.apply()
    async def get_local_config(self) -> Mapping[str, str]:
        """Get local configuration from the agent."""
        async with self._with_connection() as rpc:
            return await rpc.call.get_local_config(self.agent_id)
