from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

from ai.backend.common.docker import ImageRef
from ai.backend.common.metrics.metric import DomainType, LayerType
from ai.backend.common.resilience.policies.metrics import MetricArgs, MetricPolicy
from ai.backend.common.resilience.resilience import Resilience
from ai.backend.common.types import (
    AgentId,
    ClusterInfo,
    ImageConfig,
    KernelCreationConfig,
    KernelId,
    SessionId,
)
from ai.backend.logging import BraceStyleAdapter

from .abc import BackendAIClient

if TYPE_CHECKING:
    from ai.backend.manager.agent_cache import PeerInvoker

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

agent_client_resilience = Resilience(
    policies=[
        MetricPolicy(MetricArgs(domain=DomainType.CLIENT, layer=LayerType.AGENT_CLIENT)),
    ]
)


class AgentClient(BackendAIClient):
    """
    Client for communicating with a single agent via RPC.

    Created by AgentClientPool and holds a persistent PeerInvoker connection.
    """

    _peer: PeerInvoker
    _agent_id: AgentId

    def __init__(
        self,
        peer: PeerInvoker,
        agent_id: AgentId,
    ) -> None:
        self._peer = peer
        self._agent_id = agent_id

    @property
    def agent_id(self) -> AgentId:
        return self._agent_id

    async def connect(self) -> None:
        """Establish connection to the agent."""
        await self._peer.__aenter__()

    async def close(self) -> None:
        """Close connection to the agent."""
        try:
            await self._peer.__aexit__(None, None, None)
        except Exception:
            pass

    async def ping(self) -> str:
        """Ping the agent to check connection health."""
        return await self._peer.call.ping("ping")

    # Hardware information methods
    @agent_client_resilience.apply()
    async def health(self) -> Mapping[str, Any]:
        """Get lightweight health information from the agent."""
        return cast(Mapping[str, Any], await self._peer.call.health())

    @agent_client_resilience.apply()
    async def gather_hwinfo(self) -> Mapping[str, Any]:
        """Gather hardware information from the agent."""
        return cast(Mapping[str, Any], await self._peer.call.gather_hwinfo(agent_id=self.agent_id))

    @agent_client_resilience.apply()
    async def scan_gpu_alloc_map(self) -> Mapping[str, Any]:
        """Scan GPU allocation map from the agent."""
        return cast(Mapping[str, Any], await self._peer.call.scan_gpu_alloc_map(agent_id=self.agent_id))

    # Image management methods
    @agent_client_resilience.apply()
    async def check_and_pull(self, image_configs: Mapping[str, ImageConfig]) -> Mapping[str, str]:
        """Check and pull images on the agent."""
        return cast(Mapping[str, str], await self._peer.call.check_and_pull(image_configs, agent_id=self.agent_id))

    @agent_client_resilience.apply()
    async def purge_images(
        self,
        images: list[str],
        force: bool,
        noprune: bool,
    ) -> Mapping[str, Any]:
        """Purge images from the agent."""
        return cast(Mapping[str, Any], await self._peer.call.purge_images(images, force, noprune, agent_id=self.agent_id))

    # Network management methods
    @agent_client_resilience.apply()
    async def create_local_network(self, network_name: str) -> None:
        """Create a local network on the agent."""
        await self._peer.call.create_local_network(network_name, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def destroy_local_network(self, network_ref_name: str) -> None:
        """Destroy a local network on the agent."""
        await self._peer.call.destroy_local_network(network_ref_name, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def assign_port(self) -> int:
        """Assign a host port on the agent."""
        return await self._peer.call.assign_port(agent_id=self.agent_id)

    # Kernel management methods
    @agent_client_resilience.apply()
    async def create_kernels(
        self,
        session_id: SessionId,
        kernel_ids: list[KernelId],
        kernel_configs: list[KernelCreationConfig],
        cluster_info: ClusterInfo,
        kernel_image_refs: Mapping[KernelId, ImageRef],
    ) -> Any:
        """Create kernels on the agent."""
        return await self._peer.call.create_kernels(
            str(session_id),
            [str(kid) for kid in kernel_ids],
            kernel_configs,
            cluster_info,
            kernel_image_refs,
            agent_id=self.agent_id,
        )

    @agent_client_resilience.apply()
    async def destroy_kernel(
        self,
        kernel_id: KernelId,
        session_id: SessionId,
        reason: str,
        suppress_events: bool = True,
    ) -> None:
        """Destroy a kernel on the agent."""
        await self._peer.call.destroy_kernel(
            str(kernel_id),
            str(session_id),
            reason,
            suppress_events=suppress_events,
            agent_id=self.agent_id,
        )

    @agent_client_resilience.apply()
    async def restart_kernel(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        image_ref: ImageRef,
        update_config: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Restart a kernel on the agent."""
        return cast(Mapping[str, Any], await self._peer.call.restart_kernel(
            str(session_id),
            str(kernel_id),
            image_ref,
            update_config,
            agent_id=self.agent_id,
        ))

    @agent_client_resilience.apply()
    async def sync_kernel_registry(self, kernel_tuples: list[tuple[KernelId, SessionId]]) -> None:
        """Sync kernel registry on the agent."""
        raw_tuples = [(str(kid), str(sid)) for kid, sid in kernel_tuples]
        return await self._peer.call.sync_kernel_registry(raw_tuples, agent_id=self.agent_id)

    # Health monitoring methods
    @agent_client_resilience.apply()
    async def check_pulling(self, image_name: str) -> bool:
        """Check if an image is being pulled."""
        return await self._peer.call.check_pulling(image_name, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def check_creating(self, kernel_id: KernelId) -> bool:
        """Check if a kernel is being created."""
        return await self._peer.call.check_creating(str(kernel_id), agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def check_running(self, kernel_id: KernelId) -> bool:
        """Check if a kernel is running."""
        return await self._peer.call.check_running(str(kernel_id), agent_id=self.agent_id)

    # Code execution methods
    @agent_client_resilience.apply()
    async def execute(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        major_api_version: int,
        run_id: str,
        mode: str,
        code: str,
        opts: Mapping[str, Any],
        flush_timeout: float | None,
    ) -> Mapping[str, Any]:
        """Execute code on the agent."""
        return cast(Mapping[str, Any], await self._peer.call.execute(
            str(session_id),
            str(kernel_id),
            major_api_version,
            run_id,
            mode,
            code,
            opts,
            flush_timeout,
            agent_id=self.agent_id,
        ))

    @agent_client_resilience.apply()
    async def interrupt_kernel(self, kernel_id: KernelId) -> Mapping[str, Any]:
        """Interrupt a kernel on the agent."""
        return cast(Mapping[str, Any], await self._peer.call.interrupt_kernel(str(kernel_id), agent_id=self.agent_id))

    @agent_client_resilience.apply()
    async def trigger_batch_execution(
        self,
        session_id: SessionId,
        kernel_id: KernelId,
        startup_command: str,
        batch_timeout: float | None,
    ) -> None:
        """Trigger batch execution on the agent."""
        await self._peer.call.trigger_batch_execution(
            str(session_id),
            str(kernel_id),
            startup_command,
            batch_timeout,
            agent_id=self.agent_id,
        )

    @agent_client_resilience.apply()
    async def get_completions(
        self,
        kernel_id: KernelId,
        text: str,
        opts: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Get code completions from the agent."""
        return await self._peer.call.get_completions(
            str(kernel_id), text, opts, agent_id=self.agent_id
        )

    # Service management methods
    @agent_client_resilience.apply()
    async def start_service(
        self,
        kernel_id: KernelId,
        service: str,
        opts: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        """Start a service on the agent."""
        return cast(Mapping[str, Any], await self._peer.call.start_service(
            str(kernel_id), service, opts, agent_id=self.agent_id
        ))

    @agent_client_resilience.apply()
    async def shutdown_service(self, kernel_id: KernelId, service: str) -> None:
        """Shutdown a service on the agent."""
        await self._peer.call.shutdown_service(str(kernel_id), service, agent_id=self.agent_id)

    # File management methods
    @agent_client_resilience.apply()
    async def upload_file(
        self, kernel_id: KernelId, filename: str, payload: bytes
    ) -> Mapping[str, Any]:
        """Upload a file to the agent."""
        return cast(Mapping[str, Any], await self._peer.call.upload_file(
            str(kernel_id), filename, payload, agent_id=self.agent_id
        ))

    @agent_client_resilience.apply()
    async def download_file(self, kernel_id: KernelId, filepath: str) -> bytes:
        """Download a file from the agent."""
        return await self._peer.call.download_file(str(kernel_id), filepath, agent_id=self.agent_id)

    @agent_client_resilience.apply()
    async def download_single(self, kernel_id: KernelId, filepath: str) -> bytes:
        """Download a single file from the agent."""
        return await self._peer.call.download_single(
            str(kernel_id), filepath, agent_id=self.agent_id
        )

    @agent_client_resilience.apply()
    async def list_files(self, kernel_id: KernelId, path: str) -> Mapping[str, Any]:
        """List files on the agent."""
        return cast(Mapping[str, Any], await self._peer.call.list_files(str(kernel_id), path, agent_id=self.agent_id))

    # Log management methods
    @agent_client_resilience.apply()
    async def get_logs(self, kernel_id: KernelId) -> Mapping[str, str]:
        """Get logs from the agent."""
        return cast(Mapping[str, str], await self._peer.call.get_logs(str(kernel_id), agent_id=self.agent_id))

    # Image commit methods
    @agent_client_resilience.apply()
    async def commit(
        self,
        kernel_id: KernelId,
        email: str,
        canonical: str | None = None,
        extra_labels: dict[str, str] | None = None,
        filename: str | None = None,
    ) -> Mapping[str, Any]:
        """Commit a kernel image on the agent."""
        kwargs: dict[str, Any] = {}
        if canonical is not None:
            kwargs["canonical"] = canonical
        if extra_labels is not None:
            kwargs["extra_labels"] = extra_labels
        if filename is not None:
            kwargs["filename"] = filename
        kwargs["agent_id"] = self.agent_id

        return cast(Mapping[str, Any], await self._peer.call.commit(str(kernel_id), email, **kwargs))

    @agent_client_resilience.apply()
    async def push_image(self, image_ref: ImageRef, registry: Any) -> Mapping[str, Any]:
        """Push an image from the agent."""
        return cast(Mapping[str, Any], await self._peer.call.push_image(image_ref, registry, agent_id=self.agent_id))

    # Scaling group management
    @agent_client_resilience.apply()
    async def update_scaling_group(self, scaling_group: str) -> None:
        """Update scaling group on the agent."""
        await self._peer.call.update_scaling_group(scaling_group, self.agent_id)

    # Local configuration management
    @agent_client_resilience.apply()
    async def get_local_config(self) -> Mapping[str, str]:
        """Get local configuration from the agent."""
        return cast(Mapping[str, str], await self._peer.call.get_local_config(self.agent_id))
