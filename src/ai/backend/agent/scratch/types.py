from collections.abc import Mapping
from typing import Self

from pydantic import BaseModel

from ai.backend.common.docker import ImageRef
from ai.backend.common.types import AgentId, KernelId, ServicePort, SessionTypes

from ..kernel import KernelOwnershipData
from ..kernel_registry.types import KernelRecoveryData
from ..proxy import DomainSocketPathPair
from ..resources import KernelResourceSpec


class KernelRecoveryScratchData(BaseModel):
    """
    Serializable subset of KernelRecoveryData for scratch storage.
    Excludes `resource_spec` and `environ` which are loaded separately.

    See KernelRecoveryData in kernel_registry/types.py for field descriptions.
    """

    id: KernelId
    agent_id: AgentId
    image_ref: ImageRef
    version: int  # TODO: Consider removing versioning if not needed in future
    ownership_data: KernelOwnershipData
    network_id: str
    network_driver: str
    session_type: SessionTypes

    block_service_ports: bool
    domain_socket_proxies: list[DomainSocketPathPair]
    service_ports: list[ServicePort]
    repl_in_port: int
    repl_out_port: int

    @classmethod
    def from_kernel_recovery_data(
        cls,
        data: KernelRecoveryData,
    ) -> Self:
        return cls(
            id=data.id,
            agent_id=data.agent_id,
            image_ref=data.image_ref,
            version=data.version,
            ownership_data=data.ownership_data,
            network_id=data.network_id,
            network_driver=data.network_driver,
            session_type=data.session_type,
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
            id=self.id,
            agent_id=self.agent_id,
            image_ref=self.image_ref,
            version=self.version,
            ownership_data=self.ownership_data,
            network_id=self.network_id,
            network_driver=self.network_driver,
            session_type=self.session_type,
            block_service_ports=self.block_service_ports,
            domain_socket_proxies=self.domain_socket_proxies,
            service_ports=self.service_ports,
            repl_in_port=self.repl_in_port,
            repl_out_port=self.repl_out_port,
            resource_spec=resource_spec,
            environ=environ,
        )
