from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Final, Self

from pydantic import Field

from ai.backend.agent.kernel import AbstractKernel, KernelOwnershipData
from ai.backend.agent.kernel_registry.exception import UnsupportedKernelType
from ai.backend.agent.proxy import DomainSocketPathPair
from ai.backend.agent.resources import KernelResourceSpec
from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, BackendAISchema, KernelId, ServicePort, SessionTypes

if TYPE_CHECKING:
    from ai.backend.agent.docker.kernel import DockerKernel

#: The kernel class every record written before `KernelRecoveryData.kernel_type` came from.
DOCKER_KERNEL_TYPE: Final = "docker"


class KernelRecoveryData(BackendAISchema):
    """
    Data required for recovering a Kernel.
    Agent should load and write Kernel data using this structure
    rather than directly manipulating AbstractKernel instances.
    """

    #: Which kernel class this record was written from, and which one to rebuild it as.
    #:
    #: A record from before this field carries none, and reads as ``docker`` -- the only backend
    #: that ever wrote one. Without it a restore hands every backend a `DockerKernel`, which for
    #: anything but Docker is a kernel object whose runtime methods belong to another runtime.
    kernel_type: str = Field(default=DOCKER_KERNEL_TYPE, description="Kernel class of this record")
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

    @classmethod
    def from_kernel(cls, kernel: AbstractKernel) -> Self:
        """Write a kernel down, whatever runtime it belongs to.

        A backend added later adds its case here and to `to_kernel`. Both raise on a type they do
        not know rather than returning nothing: a registry that quietly skips a backend's kernels
        loses them at the next restart, and reports the same "saved" it does when it saved them.
        """
        from ai.backend.agent.docker.kernel import DockerKernel

        match kernel:
            case DockerKernel():
                return cls.from_docker_kernel(kernel)
            case _:
                raise UnsupportedKernelType(
                    f"{type(kernel).__name__} has no recovery record; add its case to"
                    " KernelRecoveryData.from_kernel/to_kernel before the backend can be restarted"
                    " with sessions running"
                )

    def to_kernel(self) -> AbstractKernel:
        """Rebuild the kernel this record was written from, as its own class."""
        match self.kernel_type:
            case _ if self.kernel_type == DOCKER_KERNEL_TYPE:
                return self.to_docker_kernel()
            case _:
                raise UnsupportedKernelType(
                    f"this node holds a recovery record of kernel type {self.kernel_type!r}, which"
                    " this agent cannot rebuild; it was written by a build that knows a backend"
                    " this one does not"
                )

    @classmethod
    def from_docker_kernel(cls, kernel: DockerKernel) -> Self:
        return cls(
            kernel_type=DOCKER_KERNEL_TYPE,
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
