from collections.abc import Mapping
from typing import Optional, Self

from pydantic import BaseModel, Field

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, ContainerId, KernelId, ServicePort, SessionTypes

from ..kernel import KernelLifecycleStatus, KernelOwnershipData
from ..kernel_registry.types import KernelRecoveryData
from ..proxy import DomainSocketPathPair
from ..resources import KernelResourceSpec
from ..types import AgentBackend


class KernelRecoveryDataSchema(BaseModel):
    """
    Data structure for kernel recovery data loaded from `recovery.json` file.
    This includes all KernelRecoveryData fields except for resource_spec and environ,
    which need to be loaded separately.
    """

    kernel_backend: AgentBackend
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
    container_id: Optional[ContainerId] = Field(
        description="Container ID if the kernel has an associated container"
    )
    session_type: SessionTypes = Field(description="Type of session associated with the kernel")
    state: KernelLifecycleStatus = Field(description="Lifecycle status of the kernel")

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

    @classmethod
    def from_kernel_recovery_data(
        cls,
        data: KernelRecoveryData,
    ) -> Self:
        return cls(
            kernel_backend=data.kernel_backend,
            id=data.id,
            agent_id=data.agent_id,
            image_ref=data.image_ref,
            version=data.version,
            ownership_data=data.ownership_data,
            network_id=data.network_id,
            network_driver=data.network_driver,
            container_id=data.container_id,
            session_type=data.session_type,
            state=data.state,
            block_service_ports=data.block_service_ports,
            domain_socket_proxies=data.domain_socket_proxies,
            service_ports=data.service_ports,
            repl_in_port=data.repl_in_port,
            repl_out_port=data.repl_out_port,
        )

    def to_kernel_recovery_data(
        self,
        resource_spec: KernelResourceSpec,
        environ: Mapping[str, str],
    ) -> KernelRecoveryData:
        return KernelRecoveryData(
            kernel_backend=self.kernel_backend,
            id=self.id,
            agent_id=self.agent_id,
            image_ref=self.image_ref,
            version=self.version,
            ownership_data=self.ownership_data,
            network_id=self.network_id,
            network_driver=self.network_driver,
            container_id=self.container_id,
            session_type=self.session_type,
            state=self.state,
            block_service_ports=self.block_service_ports,
            domain_socket_proxies=self.domain_socket_proxies,
            service_ports=self.service_ports,
            repl_in_port=self.repl_in_port,
            repl_out_port=self.repl_out_port,
            resource_spec=resource_spec,
            environ=environ,
        )
