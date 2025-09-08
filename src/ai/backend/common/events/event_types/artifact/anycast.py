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
class ModelsMetadataFetchDoneEvent(BaseArtifactEvent):
    models: list[ModelMetadataInfo]

    @classmethod
    @override
    def event_name(cls) -> str:
        return "models_metadata_fetch_done"

    def serialize(self) -> tuple:
        """Serialize the event data to tuple"""
        return (
            tuple(
                (
                    model.model_id,
                    model.revision,
                    model.readme_content,
                    model.registry_name,
                    model.registry_type,
                    model.size,
                )
                for model in self.models
            ),
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            models=[
                ModelMetadataInfo(
                    model_id=m[0],
                    revision=m[1],
                    readme_content=m[2],
                    registry_name=m[3],
                    registry_type=m[4],
                    size=m[5],
                )
                for m in value[0]
            ]
        )

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None
