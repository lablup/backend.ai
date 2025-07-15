from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Mapping

from ai.backend.common.types import AgentId
from ai.backend.logging import BraceStyleAdapter

if TYPE_CHECKING:
    from ai.backend.manager.agent_cache import AgentRPCCache

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class AgentClient:
    """
    Client for communicating with a single agent via RPC.
    Wraps all RPC calls to the agent to provide a cleaner interface.
    """

    def __init__(self, agent_cache: AgentRPCCache, agent_id: AgentId) -> None:
        self._agent_cache = agent_cache
        self._agent_id = agent_id

    @property
    def agent_id(self) -> AgentId:
        return self._agent_id

    # Hardware information methods
    async def gather_hwinfo(self) -> Mapping[str, Any]:
        """Gather hardware information from the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.gather_hwinfo()

    async def scan_gpu_alloc_map(self) -> Mapping[str, Any]:
        """Scan GPU allocation map from the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.scan_gpu_alloc_map()

    # Image management methods
    async def check_and_pull(self, image_configs: Any) -> dict[str, str]:
        """Check and pull images on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.check_and_pull(image_configs)

    async def purge_images(self, images: Any, force: bool, noprune: bool) -> Any:
        """Purge images from the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.purge_images(images, force, noprune)

    # Network management methods
    async def create_local_network(self, network_name: str) -> None:
        """Create a local network on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            await rpc.call.create_local_network(network_name)

    async def destroy_local_network(self, network_ref_name: str) -> None:
        """Destroy a local network on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            await rpc.call.destroy_local_network(network_ref_name)

    async def assign_port(self) -> int:
        """Assign a host port on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.assign_port()

    # Kernel management methods
    async def create_kernels(
        self,
        session_id: str,
        kernel_ids: Any,
        kernel_configs: Any,
        cluster_info: Any,
        kernel_image_refs: Any,
    ) -> Any:
        """Create kernels on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.create_kernels(
                session_id,
                kernel_ids,
                kernel_configs,
                cluster_info,
                kernel_image_refs,
            )

    async def destroy_kernel(
        self,
        kernel_id: str,
        session_id: str,
        reason: str,
        suppress_events: bool = True,
    ) -> None:
        """Destroy a kernel on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            await rpc.call.destroy_kernel(
                kernel_id,
                session_id,
                reason,
                suppress_events=suppress_events,
            )

    async def restart_kernel(
        self,
        session_id: str,
        kernel_id: str,
        image_ref: Any,
        kernel_config: Any,
    ) -> Any:
        """Restart a kernel on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.restart_kernel(
                session_id,
                kernel_id,
                image_ref,
                kernel_config,
            )

    async def sync_kernel_registry(self, kernel_tuples: Any) -> Any:
        """Sync kernel registry on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.sync_kernel_registry(kernel_tuples)

    async def drop_kernel_registry(self, kernel_id_list: Any) -> None:
        """Drop kernel registry entries on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            await rpc.call.drop_kernel_registry(kernel_id_list)

    # Container management methods
    async def purge_containers(self, serialized_data: Any) -> None:
        """Purge containers on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            await rpc.call.purge_containers(serialized_data)

    # Code execution methods
    async def execute(
        self,
        session_id: str,
        kernel_id: str,
        major_api_version: int,
        run_id: str,
        mode: str,
        code: str,
        opts: Any,
        flush_timeout: float | None,
    ) -> Mapping[str, Any]:
        """Execute code on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.execute(
                session_id,
                kernel_id,
                major_api_version,
                run_id,
                mode,
                code,
                opts,
                flush_timeout,
            )

    async def interrupt_kernel(self, kernel_id: str) -> Mapping[str, Any]:
        """Interrupt a kernel on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.interrupt_kernel(kernel_id)

    async def trigger_batch_execution(
        self,
        session_id: str,
        kernel_id: str,
        startup_command: str,
        batch_timeout: float,
    ) -> None:
        """Trigger batch execution on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            await rpc.call.trigger_batch_execution(
                session_id,
                kernel_id,
                startup_command,
                batch_timeout,
            )

    async def get_completions(
        self,
        kernel_id: str,
        text: str,
        opts: Any,
    ) -> Any:
        """Get code completions from the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.get_completions(kernel_id, text, opts)

    # Service management methods
    async def start_service(
        self,
        kernel_id: str,
        service: str,
        opts: Any,
    ) -> Mapping[str, Any]:
        """Start a service on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.start_service(kernel_id, service, opts)

    async def shutdown_service(
        self,
        kernel_id: str,
        service: str,
    ) -> None:
        """Shutdown a service on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            await rpc.call.shutdown_service(kernel_id, service)

    # File management methods
    async def upload_file(
        self,
        kernel_id: str,
        filename: str,
        payload: Any,
    ) -> Mapping[str, Any]:
        """Upload a file to the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.upload_file(kernel_id, filename, payload)

    async def download_file(
        self,
        kernel_id: str,
        filepath: str,
    ) -> bytes:
        """Download a file from the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.download_file(kernel_id, filepath)

    async def download_single(
        self,
        kernel_id: str,
        filepath: str,
    ) -> bytes:
        """Download a single file from the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.download_single(kernel_id, filepath)

    async def list_files(
        self,
        kernel_id: str,
        path: str,
    ) -> Mapping[str, Any]:
        """List files on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.list_files(kernel_id, path)

    # Log management methods
    async def get_logs(self, kernel_id: str) -> dict:
        """Get logs from the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.get_logs(kernel_id)

    # Image commit methods
    async def commit(
        self,
        kernel_id: str,
        email: str,
        canonical: str | None = None,
        extra_labels: dict[str, str] | None = None,
        filename: str | None = None,
    ) -> Mapping[str, Any]:
        """Commit a kernel image on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            kwargs: dict[str, Any] = {}
            if canonical is not None:
                kwargs["canonical"] = canonical
            if extra_labels is not None:
                kwargs["extra_labels"] = extra_labels
            if filename is not None:
                kwargs["filename"] = filename

            return await rpc.call.commit(kernel_id, email, **kwargs)

    async def push_image(
        self,
        image_ref: str,
        registry: Any,
    ) -> Mapping[str, Any]:
        """Push an image from the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.push_image(image_ref, registry)

    # Scaling group management
    async def update_scaling_group(self, scaling_group: str) -> None:
        """Update scaling group on the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            await rpc.call.update_scaling_group(scaling_group)

    # Local configuration management
    async def get_local_config(self) -> Mapping[str, str]:
        """Get local configuration from the agent."""
        async with self._agent_cache.rpc_context(self._agent_id) as rpc:
            return await rpc.call.get_local_config()
