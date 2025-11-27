"""
Standalone Agent RPC Client for REPL usage.

This module provides a minimal RPC client for connecting to Backend.AI agents
and calling their RPC functions interactively.

The agent binds (acts as server) and this client connects to it (manager role).
This matches production architecture where managers connect to agents on-demand.

Example usage:
    >>> from tools.agent_rpc_client import StandaloneAgentClient
    >>> async with StandaloneAgentClient("tcp://localhost:6001") as client:
    ...     health = await client.health()
    ...     hwinfo = await client.gather_hwinfo()
    ...     config = await client.get_local_config()
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Optional, Sequence
from uuid import UUID

import zmq
from callosum.lower.zeromq import ZeroMQAddress, ZeroMQRPCTransport
from callosum.rpc import Peer

from ai.backend.common import msgpack  # pants: no-infer-dep
from ai.backend.common.auth import ManagerAuthHandler, PublicKey, SecretKey  # pants: no-infer-dep
from ai.backend.common.docker import ImageRef  # pants: no-infer-dep
from ai.backend.common.types import AgentId, ImageConfig, KernelId  # pants: no-infer-dep
from ai.backend.logging import BraceStyleAdapter  # pants: no-infer-dep

log = BraceStyleAdapter(logging.getLogger(__name__))


class _CallStub:
    """Helper class to dynamically create RPC method calls."""

    _cached_funcs: dict[str, Any]

    def __init__(self, peer: Peer) -> None:
        self._cached_funcs = {}
        self.peer = peer

    def __getattr__(self, name: str) -> Any:
        if f := self._cached_funcs.get(name, None):
            return f

        async def _wrapped(*args: Any, **kwargs: Any) -> Any:
            request_body = {
                "args": args,
                "kwargs": kwargs,
            }
            ret = await self.peer.invoke(name, request_body)
            return ret

        self._cached_funcs[name] = _wrapped
        return _wrapped


class StandaloneAgentClient:
    """
    Standalone Agent RPC client for connecting TO an agent.

    This client CONNECTS to the agent's bind address (manager role).
    Use this when you want to call RPC functions on a running agent.

    Args:
        agent_addr: ZeroMQ address where agent is bound (e.g., "tcp://localhost:6001")
        manager_public_key: Optional manager public key for authentication
        manager_secret_key: Optional manager secret key for authentication
        agent_public_key: Optional agent public key for authentication
        invoke_timeout: Timeout for RPC calls in seconds (default: 30)
        rpc_keepalive_timeout: TCP keepalive timeout in seconds (default: 60)
    """

    def __init__(
        self,
        agent_addr: str,
        *,
        manager_public_key: Optional[PublicKey] = None,
        manager_secret_key: Optional[SecretKey] = None,
        agent_public_key: Optional[PublicKey] = None,
        invoke_timeout: float = 30.0,
        rpc_keepalive_timeout: int = 60,
    ) -> None:
        self.agent_addr = agent_addr
        self.manager_public_key = manager_public_key
        self.manager_secret_key = manager_secret_key
        self.agent_public_key = agent_public_key
        self.invoke_timeout = invoke_timeout
        self.rpc_keepalive_timeout = rpc_keepalive_timeout

        self._peer: Optional[Peer] = None
        self._call_stub: Optional[_CallStub] = None

    async def connect(self) -> None:
        """Establish connection to the agent."""
        keepalive_retry_count = 3
        keepalive_interval = self.rpc_keepalive_timeout // keepalive_retry_count
        if keepalive_interval < 2:
            keepalive_interval = 2

        auth_handler = None
        if self.agent_public_key and self.manager_public_key and self.manager_secret_key:
            auth_handler = ManagerAuthHandler(
                "local",
                self.agent_public_key,
                self.manager_public_key,
                self.manager_secret_key,
            )

        self._peer = Peer(
            connect=ZeroMQAddress(self.agent_addr),  # CONNECT to agent
            transport=ZeroMQRPCTransport,
            authenticator=auth_handler,
            transport_opts={
                "zsock_opts": {
                    zmq.TCP_KEEPALIVE: 1,
                    zmq.TCP_KEEPALIVE_IDLE: self.rpc_keepalive_timeout,
                    zmq.TCP_KEEPALIVE_INTVL: keepalive_interval,
                    zmq.TCP_KEEPALIVE_CNT: keepalive_retry_count,
                },
            },
            serializer=msgpack.packb,
            deserializer=msgpack.unpackb,
        )
        await self._peer.__aenter__()
        self._call_stub = _CallStub(self._peer)

    async def close(self) -> None:
        """Close the connection to the agent."""
        if self._peer:
            await self._peer.__aexit__(None, None, None)
            self._peer = None
            self._call_stub = None

    async def __aenter__(self) -> StandaloneAgentClient:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    @property
    def _call(self) -> _CallStub:
        """Get the call stub for making RPC calls."""
        if self._call_stub is None:
            raise RuntimeError("Client not connected. Call connect() or use as context manager.")
        return self._call_stub

    # ==================== Health & Monitoring ====================

    async def health(self) -> Mapping[str, Any]:
        """Get lightweight health information from the agent."""
        return await self._call.health()

    async def gather_hwinfo(self, agent_id: Optional[AgentId] = None) -> Mapping[str, Any]:
        """Gather hardware information from the agent."""
        return await self._call.gather_hwinfo(agent_id=agent_id)

    async def ping_kernel(self, kernel_id: str, agent_id: Optional[AgentId] = None) -> None:
        """Ping a kernel to check if it's responsive."""
        return await self._call.ping_kernel(kernel_id, agent_id=agent_id)

    # ==================== Image Management ====================

    async def check_and_pull(
        self,
        image_configs: Mapping[str, ImageConfig],
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Check if images exist and pull them if necessary."""
        return await self._call.check_and_pull(image_configs, agent_id=agent_id)

    async def purge_images(
        self,
        image_canonicals: list[str],
        force: bool,
        noprune: bool,
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Purge specified images from the agent."""
        return await self._call.purge_images(image_canonicals, force, noprune, agent_id=agent_id)

    async def push_image(
        self,
        image_ref: ImageRef,
        registry_conf: Mapping[str, Any],
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Push an image to a registry."""
        return await self._call.push_image(image_ref, registry_conf, agent_id=agent_id)

    # ==================== Kernel Lifecycle ====================

    async def create_kernels(
        self,
        raw_session_id: str,
        raw_kernel_ids: Sequence[str],
        raw_configs: Sequence[dict],
        raw_cluster_info: dict,
        kernel_image_refs: dict[KernelId, ImageRef],
        agent_id: Optional[AgentId] = None,
    ) -> Any:
        """Create kernels on the agent."""
        return await self._call.create_kernels(
            raw_session_id,
            raw_kernel_ids,
            raw_configs,
            raw_cluster_info,
            kernel_image_refs,
            agent_id=agent_id,
        )

    async def destroy_kernel(
        self,
        kernel_id: str,
        session_id: str,
        reason: Optional[str] = None,
        suppress_events: bool = False,
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Destroy a kernel."""
        return await self._call.destroy_kernel(
            kernel_id,
            session_id,
            reason=reason,
            suppress_events=suppress_events,
            agent_id=agent_id,
        )

    async def restart_kernel(
        self,
        session_id: str,
        kernel_id: str,
        kernel_image: ImageRef,
        updated_config: dict,
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Restart a kernel."""
        return await self._call.restart_kernel(
            session_id,
            kernel_id,
            kernel_image,
            updated_config,
            agent_id=agent_id,
        )

    # ==================== Kernel Operations ====================

    async def execute(
        self,
        session_id: str,
        kernel_id: str,
        api_version: int,
        run_id: str,
        mode: str,
        code: str,
        opts: dict[str, Any],
        flush_timeout: float,
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Execute code in a kernel."""
        return await self._call.execute(
            session_id,
            kernel_id,
            api_version,
            run_id,
            mode,
            code,
            opts,
            flush_timeout,
            agent_id=agent_id,
        )

    async def interrupt_kernel(self, kernel_id: str, agent_id: Optional[AgentId] = None) -> None:
        """Interrupt a running kernel."""
        return await self._call.interrupt_kernel(kernel_id, agent_id=agent_id)

    async def get_completions(
        self,
        kernel_id: str,
        text: str,
        opts: Mapping[str, Any],
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Get code completions for a kernel."""
        return await self._call.get_completions(kernel_id, text, opts, agent_id=agent_id)

    async def trigger_batch_execution(
        self,
        session_id: str,
        kernel_id: str,
        code: str,
        timeout: Optional[float],
        agent_id: Optional[AgentId] = None,
    ) -> None:
        """Trigger batch execution for a kernel."""
        return await self._call.trigger_batch_execution(
            session_id, kernel_id, code, timeout, agent_id=agent_id
        )

    async def get_logs(
        self,
        kernel_id: str,
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Get logs from a kernel."""
        return await self._call.get_logs(kernel_id, agent_id=agent_id)

    # ==================== File Operations ====================

    async def upload_file(
        self,
        kernel_id: str,
        filename: str,
        filedata: bytes,
        agent_id: Optional[AgentId] = None,
    ) -> None:
        """Upload a file to a kernel."""
        return await self._call.upload_file(kernel_id, filename, filedata, agent_id=agent_id)

    async def download_file(
        self,
        kernel_id: str,
        filepath: str,
        agent_id: Optional[AgentId] = None,
    ) -> bytes:
        """Download a file from a kernel."""
        return await self._call.download_file(kernel_id, filepath, agent_id=agent_id)

    async def download_single(
        self,
        kernel_id: str,
        filepath: str,
        agent_id: Optional[AgentId] = None,
    ) -> bytes:
        """Download a single file from a kernel."""
        return await self._call.download_single(kernel_id, filepath, agent_id=agent_id)

    async def list_files(
        self,
        kernel_id: str,
        path: str,
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """List files in a kernel directory."""
        return await self._call.list_files(kernel_id, path, agent_id=agent_id)

    # ==================== Network Operations ====================

    async def create_local_network(
        self,
        network_name: str,
        agent_id: Optional[AgentId] = None,
    ) -> None:
        """Create a local network on the agent."""
        return await self._call.create_local_network(network_name, agent_id=agent_id)

    async def destroy_local_network(
        self,
        network_name: str,
        agent_id: Optional[AgentId] = None,
    ) -> None:
        """Destroy a local network on the agent."""
        return await self._call.destroy_local_network(network_name, agent_id=agent_id)

    async def assign_port(
        self,
        agent_id: Optional[AgentId] = None,
    ) -> int:
        """Assign a port on the agent."""
        return await self._call.assign_port(agent_id=agent_id)

    async def release_port(
        self,
        port_no: int,
        agent_id: Optional[AgentId] = None,
    ) -> None:
        """Release a port on the agent."""
        return await self._call.release_port(port_no, agent_id=agent_id)

    # ==================== Container Operations ====================

    async def purge_containers(
        self,
        container_kernel_ids: list[tuple[str, str]],
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Purge containers from the agent."""
        return await self._call.purge_containers(container_kernel_ids, agent_id=agent_id)

    async def commit(
        self,
        kernel_id: str,
        subdir: str,
        canonical: Optional[str] = None,
        filename: Optional[str] = None,
        extra_labels: dict[str, str] = {},
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Commit a kernel as a new image."""
        return await self._call.commit(
            kernel_id,
            subdir,
            canonical=canonical,
            filename=filename,
            extra_labels=extra_labels,
            agent_id=agent_id,
        )

    # ==================== Configuration & Management ====================

    async def get_local_config(
        self,
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Get local configuration from the agent."""
        return await self._call.get_local_config(agent_id=agent_id)

    async def update_scaling_group(
        self,
        scaling_group: str,
        agent_id: Optional[AgentId] = None,
    ) -> None:
        """Update the scaling group for the agent."""
        return await self._call.update_scaling_group(scaling_group, agent_id=agent_id)

    # ==================== Service Management ====================

    async def start_service(
        self,
        kernel_id: str,
        service: str,
        opts: Mapping[str, Any],
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Start a service in a kernel."""
        return await self._call.start_service(kernel_id, service, opts, agent_id=agent_id)

    async def shutdown_service(
        self,
        kernel_id: str,
        service: str,
        agent_id: Optional[AgentId] = None,
    ) -> None:
        """Shutdown a service in a kernel."""
        return await self._call.shutdown_service(kernel_id, service, agent_id=agent_id)

    # ==================== Registry Operations ====================

    async def sync_kernel_registry(
        self,
        raw_kernel_session_ids: Sequence[tuple[str, str]],
        agent_id: Optional[AgentId] = None,
    ) -> None:
        """Sync kernel registry data."""
        return await self._call.sync_kernel_registry(
            raw_kernel_session_ids,
            agent_id=agent_id,
        )

    async def drop_kernel_registry(
        self,
        kernel_ids: list[UUID],
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Drop kernel registry data."""
        return await self._call.drop_kernel_registry(kernel_ids, agent_id=agent_id)

    # ==================== Status Checks ====================

    async def check_pulling(
        self,
        image_name: str,
        agent_id: Optional[AgentId] = None,
    ) -> bool:
        """Check if an image is being pulled."""
        return await self._call.check_pulling(image_name, agent_id=agent_id)

    async def check_creating(
        self,
        kernel_id: str,
        agent_id: Optional[AgentId] = None,
    ) -> bool:
        """Check if a kernel is being created."""
        return await self._call.check_creating(kernel_id, agent_id=agent_id)

    async def check_running(
        self,
        kernel_id: str,
        agent_id: Optional[AgentId] = None,
    ) -> bool:
        """Check if a kernel is running."""
        return await self._call.check_running(kernel_id, agent_id=agent_id)

    # ==================== GPU & Resource Management ====================

    async def scan_gpu_alloc_map(
        self,
        agent_id: Optional[AgentId] = None,
    ) -> Mapping[str, Any]:
        """Scan GPU allocation map."""
        return await self._call.scan_gpu_alloc_map(agent_id=agent_id)

    # ==================== Agent Control ====================

    async def shutdown_agent(
        self, terminate_kernels: bool, agent_id: Optional[AgentId] = None
    ) -> None:
        """Shutdown the agent."""
        return await self._call.shutdown_agent(terminate_kernels, agent_id=agent_id)

    async def reset_agent(self, agent_id: Optional[AgentId] = None) -> None:
        """Reset the agent."""
        return await self._call.reset_agent(agent_id=agent_id)
