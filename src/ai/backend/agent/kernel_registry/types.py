from collections.abc import Mapping
from typing import Optional

from pydantic import BaseModel

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

    kernel_backend: AgentBackend

    id: KernelId
    agent_id: AgentId
    image_ref: ImageRef
    version: int
    ownership_data: KernelOwnershipData
    network_id: str
    network_driver: str
    container_id: Optional[ContainerId]
    session_type: SessionTypes
    state: KernelLifecycleStatus

    block_service_ports: bool
    domain_socket_proxies: list[DomainSocketProxy]
    service_ports: list[ServicePort]
    repl_in_port: int
    repl_out_port: int
    resource_spec: KernelResourceSpec
    environ: Mapping[str, str]
