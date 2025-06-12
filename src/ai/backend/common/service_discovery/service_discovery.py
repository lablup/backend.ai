import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional, Self, Sequence

from pydantic import BaseModel, Field

from ai.backend.common.types import ServiceDiscoveryType
from ai.backend.logging.utils import BraceStyleAdapter

_DEFAULT_HEARTBEAT_TIMEOUT = 60 * 5  # 5 minutes
_DEFAULT_SWEEP_INTERVAL = 60 * 10  # 10 minutes

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class ServiceEndpoint(BaseModel):
    """
    Service endpoint.
    """

    address: str
    port: int
    protocol: str
    prometheus_address: str


class HealthStatus(BaseModel):
    """
    Health status of a service.
    """

    registration_time: float = Field(default_factory=time.time)
    last_heartbeat: float = Field(default_factory=time.time)

    def check_healthy(self, timeout: float = _DEFAULT_HEARTBEAT_TIMEOUT) -> bool:
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

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, HealthStatus):
            return False
        # Heartbeat time is not considered for equality check
        return self.registration_time == value.registration_time


class ServiceMetadata(BaseModel):
    """
    Metadata for a service.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    display_name: str = Field(..., description="Display name of the service")
    service_group: str = Field(..., description="Name of the service group (manager, agent, etc.)")
    version: str = Field(..., description="Version of the service")
    endpoint: ServiceEndpoint = Field(..., description="Endpoint of the service")
    health_status: HealthStatus = Field(
        default_factory=HealthStatus, description="Health status of the service"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(**data)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert the service metadata to a dictionary.
        :return: Dictionary representation of the service metadata.
        """
        return self.model_dump()


class ServiceDiscovery(ABC):
    """
    Abstract class for service discovery.
    This class is used to discover services in a distributed system.
    """

    @abstractmethod
    async def register(self, service_meta: ServiceMetadata) -> None:
        """
        Register a service.
        :param service_meta: Service metadata.
        """
        raise NotImplementedError

    @abstractmethod
    async def unregister(self, service_group: str, service_id: uuid.UUID) -> None:
        """
        Unregister a service.
        :param service_group: Name of the service group.
        :param service_id: UUID of the service.
        """
        raise NotImplementedError

    @abstractmethod
    async def heartbeat(self, service_meta: ServiceMetadata) -> None:
        """
        Send a heartbeat to the service discovery.
        When a service is not ready in the service discovery, it registers it.
        :param service_meta: Service metadata.
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
    async def get_service(self, service_group: str, service_id: uuid.UUID) -> ServiceMetadata:
        """
        Get service address by name.
        :param service_group: Name of the service group.
        :param service_id: UUID of the service.
        :return: Service metadata.
        """
        raise NotImplementedError


class ServiceDiscoveryLoop:
    """
    Service discovery loop.
    This class is used to discover services in a distributed system.
    """

    _type: ServiceDiscoveryType
    _service_discovery: ServiceDiscovery
    _metadata: ServiceMetadata
    _interval_seconds: int
    _closed: bool = False
    _run_service_task: asyncio.Task[None]
    _sweep_unhealthy_services_task: Optional[asyncio.Task[None]]

    def __init__(
        self,
        sd_type: ServiceDiscoveryType,
        service_discovery: ServiceDiscovery,
        metadata: ServiceMetadata,
        interval_seconds: int = 60,
    ) -> None:
        self._type = sd_type
        self._service_discovery = service_discovery
        self._metadata = metadata
        self._interval_seconds = interval_seconds
        self._closed = False
        self._run_service_task = asyncio.create_task(self._run_service_loop())

        match self._type:
            case ServiceDiscoveryType.ETCD:
                self._sweep_unhealthy_services_task = asyncio.create_task(
                    self._sweep_unhealthy_services_loop()
                )
            case ServiceDiscoveryType.REDIS:
                # We can set expire time for Redis keys, so no need to sweep unhealthy services.
                self._sweep_unhealthy_services_task = None

    @property
    def metadata(self) -> ServiceMetadata:
        return self._metadata

    def close(self) -> None:
        """
        Close the service discovery loop.
        """
        if self._closed:
            return
        self._closed = True
        self._run_service_task.cancel()
        if self._sweep_unhealthy_services_task:
            self._sweep_unhealthy_services_task.cancel()

    async def _sweep_unhealthy_services_loop(self) -> None:
        """
        Sweep unhealthy services.
        This method is used to sweep unhealthy services in the service discovery.
        """
        while not self._closed:
            try:
                services = await self._service_discovery.discover()
                for service in services:
                    if not service.health_status.check_healthy():
                        await self._service_discovery.unregister(
                            service_group=service.service_group,
                            service_id=service.id,
                        )
            except Exception as e:
                log.error("Error sweeping unhealthy services: {}", e)
            await asyncio.sleep(_DEFAULT_SWEEP_INTERVAL)

    async def _run_service_loop(self) -> None:
        log.info(
            "Registering service {} with ID {} in group {}",
            self._metadata.display_name,
            self._metadata.id,
            self._metadata.service_group,
        )
        await self._service_discovery.register(self._metadata)
        while not self._closed:
            try:
                await self._service_discovery.heartbeat(
                    service_meta=self._metadata,
                )
            except Exception as e:
                log.error("Error sending heartbeat: {}", e)
            await asyncio.sleep(self._interval_seconds)
        await self._service_discovery.unregister(
            service_group=self._metadata.service_group,
            service_id=self._metadata.id,
        )
