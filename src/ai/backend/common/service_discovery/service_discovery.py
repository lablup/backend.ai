import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Self, Sequence

_DEFAULT_HEARTBEAT_TIMEOUT = 60 * 5  # 5 minutes


@dataclass
class ServiceEndpoint:
    """
    Service endpoint.
    """

    address: str
    port: int
    protocol: str
    prometheus_address: str


@dataclass
class HealthStatus:
    """
    Health status of a service.
    """

    registration_time: float
    last_heartbeat: float

    @property
    def is_healthy(self, timeout: float = _DEFAULT_HEARTBEAT_TIMEOUT) -> bool:
        """
        Check if the service is healthy.
        :return: True if the service is healthy, False otherwise.
        """
        now = time.time()
        return (now - self.last_heartbeat) < timeout

    def update_heartbeat(self) -> None:
        """
        Update the last heartbeat time.
        """
        self.last_heartbeat = time.time()


@dataclass
class ServiceMetadata:
    """
    Metadata for a service.
    """

    id: uuid.UUID
    display_name: str
    service_group: str
    version: str
    endpoint: ServiceEndpoint
    health_status: HealthStatus

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the service metadata to a dictionary.
        :return: Dictionary representation of the service metadata.
        """
        return asdict(self)


class ServiceDiscovery(ABC):
    """
    Abstract class for service discovery.
    This class is used to discover services in a distributed system.
    """

    @abstractmethod
    async def register(self, service: ServiceMetadata) -> None:
        """
        Register a service.
        :param service: Service metadata.
        """
        raise NotImplementedError

    @abstractmethod
    async def unregister(self, service_group: str, uuid: uuid.UUID) -> None:
        """
        Unregister a service.
        :param service_group: Name of the service group.
        :param uuid: UUID of the service.
        """
        raise NotImplementedError

    @abstractmethod
    async def heartbeat(self, service_group: str, uuid: uuid.UUID) -> None:
        """
        Send a heartbeat to the service discovery.
        :param service_group: Name of the service group.
        :param uuid: UUID of the service.
        """
        raise NotImplementedError

    @abstractmethod
    async def discover(self) -> Sequence[ServiceMetadata]:
        """
        Discover services.
        :return: List of service metadata.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_service_group(self, service_group: str) -> Sequence[ServiceMetadata]:
        """
        Get services by group.
        :param service_group: Name of the service group.
        :return: List of service metadata.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_service(self, service_group: str, uuid: uuid.UUID) -> ServiceMetadata:
        """
        Get service address by name.
        :param service_group: Name of the service group.
        :param uuid: UUID of the service.
        :return: Service metadata.
        """
        raise NotImplementedError
