from __future__ import annotations

from datetime import datetime
from typing import Any, override

from pydantic import Field

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import BackendAISchema

__all__ = (
    "DoSweepStaleServicesEvent",
    "ServiceEndpointInfo",
    "ServiceRegisteredEvent",
    "ServiceDeregisteredEvent",
)


class ServiceEndpointInfo(BackendAISchema):
    """Data model for a service endpoint."""

    role: str = Field(description="Role of this endpoint (e.g., 'main', 'health', 'internal').")
    scope: str = Field(
        description="Network scope of this endpoint (e.g., 'public', 'private', 'internal')."
    )
    address: str = Field(description="Hostname or IP address of the endpoint.")
    port: int = Field(description="Port number of the endpoint.")
    protocol: str = Field(
        description="Protocol used by the endpoint (e.g., 'grpc', 'http', 'https')."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the endpoint.",
    )


class BaseServiceDiscoveryEvent(AbstractAnycastEvent):
    """Base class for service discovery events."""

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SERVICE_DISCOVERY

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class ServiceRegisteredEvent(BackendAISchema, BaseServiceDiscoveryEvent):
    """Event emitted when a service instance registers or sends a heartbeat.

    Contains full service metadata and endpoint information.
    """

    instance_id: str = Field(description="Unique instance identifier.")
    service_group: str = Field(description="Logical group name for the service.")
    display_name: str = Field(description="Human-readable display name.")
    version: str = Field(description="Version of the service instance.")
    labels: dict[str, str] = Field(
        default_factory=dict,
        description="Labels for categorization and filtering.",
    )
    endpoints: list[ServiceEndpointInfo] = Field(
        default_factory=list,
        description="Endpoints exposed by this service instance.",
    )
    startup_time: datetime = Field(description="When the service instance started.")
    config_hash: str = Field(
        default="",
        description="Hash of the service configuration for change detection.",
    )

    @classmethod
    @override
    def event_name(cls) -> str:
        return "service_registered"


class DoSweepStaleServicesEvent(BaseServiceDiscoveryEvent):
    """Event to trigger sweeping stale services in the catalog."""

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_sweep_stale_services"


class ServiceDeregisteredEvent(BackendAISchema, BaseServiceDiscoveryEvent):
    """Event emitted when a service instance is deregistered."""

    instance_id: str = Field(description="Unique instance identifier.")
    service_group: str = Field(description="Logical group name for the service.")

    @classmethod
    @override
    def event_name(cls) -> str:
        return "service_deregistered"
