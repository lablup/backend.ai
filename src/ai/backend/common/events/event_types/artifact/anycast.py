from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
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


@dataclass
class ModelImportDoneEvent(BaseArtifactEvent):
    model_id: str
    revision: str
    registry_type: ArtifactRegistryType
    registry_name: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "model_import_done"

    def serialize(self) -> tuple:
        return (self.model_id, self.revision, self.registry_type, self.registry_name)

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            model_id=value[0],
            revision=value[1],
            registry_type=value[2],
            registry_name=value[3],
        )

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class ModelMetadataFetchDoneEvent(BaseArtifactEvent):
    model: ModelMetadataInfo

    @classmethod
    @override
    def event_name(cls) -> str:
        return "models_metadata_fetch_done"

    def serialize(self) -> tuple:
        return (
            self.model.model_id,
            self.model.revision,
            self.model.readme_content,
            self.model.registry_name,
            self.model.registry_type,
            self.model.size,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            model=ModelMetadataInfo(
                model_id=value[0],
                revision=value[1],
                readme_content=value[2],
                registry_name=value[3],
                registry_type=value[4],
                size=value[5],
            )
        )

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None
