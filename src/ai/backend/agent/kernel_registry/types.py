from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Self

from pydantic import Field

from ai.backend.agent.kernel import KernelOwnershipData
from ai.backend.agent.proxy import DomainSocketPathPair
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, BackendAISchema, KernelId, ServicePort, SessionTypes

if TYPE_CHECKING:
    from ai.backend.agent.containerd.kernel import ContainerdKernel
    from ai.backend.agent.docker.kernel import DockerKernel

# The containerd kernel carries no network_driver; recovery persists a placeholder to satisfy
# the shared schema (it is dropped again by to_containerd_kernel and never consumed).
_CONTAINERD_NETWORK_DRIVER_PLACEHOLDER = "bridge"


class KernelRecoveryData(BackendAISchema):
    """
    Data required for recovering a Kernel.
    Agent should load and write Kernel data using this structure
    rather than directly manipulating AbstractKernel instances.
    """

    id: KernelId = Field(description="ID of the kernel")
    agent_id: AgentId = Field(description="ID of the agent that owns the kernel")
    image_ref: ImageRef = Field(description="Docker image reference used for the kernel")
    version: int = Field()  # TODO: Consider removing versioning if not needed in future
    ownership_data: KernelOwnershipData = Field(description="Ownership data of the kernel")
    network_id: str = Field(
        description="Network ID that the kernel is connected to. It is created and managed by Manager."
    )
    network_driver: str = Field(
        description="Network driver name. It is managed by Agent-side network plugin.",
        examples=["bridge"],
    )
    session_type: SessionTypes = Field(description="Type of session associated with the kernel")

    block_service_ports: bool = Field(
        description="Whether to block service ports. If true, cannot start any service of the kernel"
    )
    domain_socket_proxies: list[DomainSocketPathPair] = Field(
        description="List of domain socket path pairs associated with the kernel"
    )
    service_ports: list[ServicePort] = Field(
        description="List of service port mappings exposed by the kernel"
    )
    repl_in_port: int = Field(
        description="REPL input port number. Should be one of the service ports"
    )
    repl_out_port: int = Field(
        description="REPL output port number. Should be one of the service ports"
    )
    resource_spec: KernelResourceSpec = Field(description="Resource specifications for the kernel")
    environ: Mapping[str, str] = Field(description="Environment variables for the kernel")
    # Optional runtime handles some backends (containerd) need to reconstruct a live kernel:
    # the container id and the host-reachable REPL address. Docker re-derives these from the
    # daemon at runtime, so they stay None there; kept backward-compatible via defaults.
    container_id: str | None = Field(default=None, description="Runtime container id, if pinned")
    kernel_host: str | None = Field(
        default=None, description="Advertised address the manager routes to, if pinned"
    )
    repl_host: str | None = Field(
        default=None,
        description=(
            "Node-local address the agent dials the REPL at, if pinned. Distinct from kernel_host: "
            "containerd gives the container a private LOCAL address and publishes only its services."
        ),
    )

    @classmethod
    def from_docker_kernel(cls, kernel: DockerKernel) -> Self:
        return cls(
            id=kernel.kernel_id,
            agent_id=kernel.agent_id,
            image_ref=kernel.image,
            session_type=kernel.session_type,
            ownership_data=kernel.ownership_data,
            network_id=kernel.network_id,
            version=kernel.version,
            network_driver=kernel.network_driver,
            resource_spec=kernel.resource_spec,
            service_ports=kernel.service_ports,
            environ=kernel.environ,
            block_service_ports=kernel.data.get("block_service_ports", False),
            domain_socket_proxies=kernel.data.get("domain_socket_proxies", []),
            repl_in_port=kernel.data["repl_in_port"],
            repl_out_port=kernel.data["repl_out_port"],
        )

    def to_docker_kernel(self) -> DockerKernel:
        from ai.backend.agent.docker.kernel import DockerKernel

        return DockerKernel(
            ownership_data=self.ownership_data,
            network_id=self.network_id,
            image=self.image_ref,
            version=self.version,
            network_driver=self.network_driver,
            agent_config={},
            resource_spec=self.resource_spec,
            service_ports=self.service_ports,
            environ=self.environ,
            data={
                "repl_in_port": self.repl_in_port,
                "repl_out_port": self.repl_out_port,
                "block_service_ports": self.block_service_ports,
                "domain_socket_proxies": self.domain_socket_proxies,
            },
        )

    @classmethod
    def from_containerd_kernel(cls, kernel: ContainerdKernel) -> Self:
        return cls(
            id=kernel.kernel_id,
            agent_id=kernel.agent_id,
            image_ref=kernel.image,
            session_type=kernel.session_type,
            ownership_data=kernel.ownership_data,
            network_id=kernel.network_id,
            version=kernel.version,
            # containerd has no network_driver; persist a placeholder for the shared schema.
            network_driver=_CONTAINERD_NETWORK_DRIVER_PLACEHOLDER,
            resource_spec=kernel.resource_spec,
            service_ports=kernel.service_ports,
            environ=kernel.environ,
            block_service_ports=kernel.data.get("block_service_ports", False),
            domain_socket_proxies=kernel.data.get("domain_socket_proxies", []),
            repl_in_port=kernel.data["repl_in_port"],
            repl_out_port=kernel.data["repl_out_port"],
            # containerd reconstructs the code runner + log path from these, so they must persist.
            container_id=kernel.data["container_id"],
            kernel_host=kernel.data["kernel_host"],
            repl_host=kernel.data.get("repl_host"),
        )

    def to_containerd_kernel(self) -> ContainerdKernel:
        from ai.backend.agent.containerd.kernel import ContainerdKernel

        return ContainerdKernel(
            ownership_data=self.ownership_data,
            network_id=self.network_id,
            image=self.image_ref,
            version=self.version,
            agent_config={},
            resource_spec=self.resource_spec,
            service_ports=self.service_ports,
            environ=self.environ,
            data={
                "repl_in_port": self.repl_in_port,
                "repl_out_port": self.repl_out_port,
                "block_service_ports": self.block_service_ports,
                "domain_socket_proxies": self.domain_socket_proxies,
                "container_id": self.container_id,
                "kernel_host": self.kernel_host,
                "repl_host": self.repl_host,
            },
        )
