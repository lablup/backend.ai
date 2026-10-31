from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, override

from pydantic import Field

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import (
    StorageBackendMetadata,
    StorageCheckState,
    StorageStatusCheckType,
)
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.common.types import BackendAISchema

__all__ = (
    "StorageStatusObservation",
    "StorageStatusReportEvent",
)


class StorageStatusObservation(BackendAISchema):
    """The latest observation of one volume, as the service holding it saw it."""

    volume_name: StorageVolumeName = Field(description="System-unique name of the volume.")
    storage_backend_metadata: StorageBackendMetadata = Field(
        description="The storage backend implementation the volume is served by."
    )
    check_type: StorageStatusCheckType = Field(
        description="Which status check the observation comes from."
    )
    check_state: StorageCheckState = Field(description="Whether a check has run yet.")
    check_started_at: datetime | None = Field(
        default=None, description="When the check started, null until one has run."
    )
    duration: timedelta | None = Field(default=None, description="How long the check took.")
    error_msg: str | None = Field(
        default=None, description="Why the observation failed, null where it succeeded."
    )
    device_id: str | None = Field(
        default=None, description="The device the volume is served from, null where unread."
    )
    extra: dict[str, Any] | None = Field(
        default=None, description="What only the check type records."
    )


class StorageStatusReportEvent(BackendAISchema, AbstractAnycastEvent):
    """Latest observations of every volume a service checks.

    Connection details and credentials are never carried: the event travels over the shared bus.
    """

    service_catalog_instance_id: str = Field(
        description="Instance id of the reporting service in the service catalog."
    )
    service_catalog_service_group: str = Field(
        description="Service group of the reporting service in the service catalog."
    )
    observations: list[StorageStatusObservation] = Field(
        default_factory=list, description="Latest observation of each checked volume."
    )

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.STORAGE_STATUS

    @classmethod
    @override
    def event_name(cls) -> str:
        return "storage_status_reported"

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None
