from collections.abc import Mapping
from typing import Optional

from pydantic import BaseModel, Field

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, ContainerId, KernelId, ServicePort, SessionTypes

from ..kernel import AbstractKernel, KernelLifecycleStatus, KernelOwnershipData
from ..proxy import DomainSocketProxy
from ..resources import KernelResourceSpec
from ..types import AgentBackend

KernelRegistryType = Mapping[KernelId, AbstractKernel]


class KernelRecoveryData(BaseModel):
    """
    Data required for recovering a Kernel.
    Agent should load and write Kernel data using this structure
    rather than directly manipulating AbstractKernel instances.
    """

    kernel_backend: AgentBackend = Field(
        description="Backend type of the kernel", examples=[AgentBackend.DOCKER]
    )

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
    domain_socket_proxies: list[DomainSocketProxy] = Field(
        description="List of domain socket proxies associated with the kernel"
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
