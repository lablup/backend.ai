from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    VerificationStepResult,
)
from ai.backend.common.events.types import (
    AbstractAnycastEvent,
    EventDomain,
)
from ai.backend.common.events.user_event.user_event import UserEvent


class BaseArtifactEvent(AbstractAnycastEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.ARTIFACT


@dataclass
class ModelMetadataInfo:
    """Individual model metadata information including README and file size"""

    model_id: str
    revision: str
    readme_content: str
    registry_type: ArtifactRegistryType
    registry_name: str
    size: int


class ModelVerifyingEvent(BaseArtifactEvent):
    """
    Mark the model revision's status to verifying.
    """

    model_id: str
    revision: str
    registry_type: ArtifactRegistryType
    registry_name: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "model_verifying"

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class ModelImportDoneEvent(BaseArtifactEvent):
    model_id: str
    revision: str
    registry_type: ArtifactRegistryType
    registry_name: str
    success: bool
    digest: str | None
    verification_result: VerificationStepResult | None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "model_import_done"

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class ModelMetadataFetchDoneEvent(BaseArtifactEvent):
    model: ModelMetadataInfo

    @classmethod
    @override
    def event_name(cls) -> str:
        return "models_metadata_fetch_done"

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None
