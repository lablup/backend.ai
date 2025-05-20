import uuid
from dataclasses import dataclass
from typing import Any, Sequence, cast

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes

from ..service_discovery import ServiceDiscovery, ServiceMetadata

_DEFAULT_PREFIX = "ai/backend/service_discovery"


@dataclass
class ETCDServiceDiscoveryArgs:
    etcd: AsyncEtcd
    prefix: str = _DEFAULT_PREFIX


class ETCDServiceDiscovery(ServiceDiscovery):
    _etcd: AsyncEtcd
    _prefix: str

    def __init__(self, args: ETCDServiceDiscoveryArgs) -> None:
        self._etcd = args.etcd
        self._prefix = args.prefix

    async def register(self, service: ServiceMetadata) -> None:
        """
        Register a service in the service discovery.
        :param service: Service metadata.
        """

        prefix = self._service_prefix(service.service_group, service.id)
        await self._etcd.put_prefix(prefix, service.to_dict(), scope=ConfigScopes.GLOBAL)

    async def unregister(self, service_group: str, service_id: uuid.UUID) -> None:
        """
        Unregister a service from the service discovery.
        :param service_group: Name of the service group.
        :param service_id: UUID of the service.
        """

        await self._etcd.delete_prefix(
            self._service_prefix(service_group, service_id), scope=ConfigScopes.GLOBAL
        )

    async def heartbeat(self, service_group: str, service_id: uuid.UUID) -> None:
        """
        Send a heartbeat to the service discovery.
        :param service_group: Name of the service group.
        :param service_id: UUID of the service.
        """

        prefix = self._service_prefix(service_group, service_id)
        raw_service_info = await self._etcd.get_prefix(prefix, scope=ConfigScopes.GLOBAL)
        if not raw_service_info:
            raise ValueError(f"Service with ID {service_id} not found.")

        service_dict = cast(dict[str, Any], raw_service_info)
        service = ServiceMetadata.from_dict(service_dict)
        service.health_status.update_heartbeat()
        await self._etcd.put_prefix(prefix, service.to_dict(), scope=ConfigScopes.GLOBAL)

    async def discover(self) -> Sequence[ServiceMetadata]:
        """
        Discover all services in the service discovery.
        :return: List of service metadata.
        """

        raw_service_groups = await self._etcd.get_prefix(self._prefix, scope=ConfigScopes.GLOBAL)
        services = []
        if not raw_service_groups:
            raise ValueError("No service groups found.")
        service_groups = cast(dict[str, dict[str, dict[str, Any]]], raw_service_groups)
        for _, service_configs in service_groups.items():
            for _, service_config in service_configs.items():
                services.append(ServiceMetadata.from_dict(service_config))
        return services

    async def get_service_group(self, service_group: str) -> Sequence[ServiceMetadata]:
        """
        Get services by group.
        :param service_group: Name of the service group.
        :return: List of service metadata.
        """

        service_group_prefix = self._service_group_prefix(service_group)
        raw_service_configs = await self._etcd.get_prefix(
            service_group_prefix, scope=ConfigScopes.GLOBAL
        )
        if not raw_service_configs:
            raise ValueError(f"No services found in group {service_group}.")
        service_configs = cast(dict[str, dict[str, Any]], raw_service_configs)
        services = []
        for _, service_config in service_configs.items():
            services.append(ServiceMetadata.from_dict(service_config))
        return services

    async def get_service(self, service_group: str, service_id: uuid.UUID) -> ServiceMetadata:
        """
        Get service address by ID.
        :param service_id: UUID of the service.
        :return: Service metadata.
        """

        service_prefix = self._service_prefix(service_group, service_id)
        raw_service_config = await self._etcd.get_prefix(service_prefix, scope=ConfigScopes.GLOBAL)
        if not raw_service_config:
            raise ValueError(f"Service with ID {service_id} not found.")
        service_config = cast(dict[str, Any], raw_service_config)
        return ServiceMetadata.from_dict(service_config)

    def _service_group_prefix(self, service_group: str) -> str:
        return f"{self._prefix}/{service_group}"

    def _service_prefix(self, service_group: str, service_id: uuid.UUID) -> str:
        return f"{self._service_group_prefix(service_group)}/{service_id}"
