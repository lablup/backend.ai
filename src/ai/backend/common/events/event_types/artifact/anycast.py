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
class ModelImportDoneEvent(BaseArtifactEvent):
    model_id: str
    revision: str
    registry_name: str
    registry_type: ArtifactRegistryType
    total_size: int

    @classmethod
    @override
    def event_name(cls) -> str:
        return "model_import_done"

    def serialize(self) -> tuple:
        return (
            self.model_id,
            self.revision,
            self.registry_name,
            self.registry_type,
            self.total_size,
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            model_id=value[0],
            revision=value[1],
            registry_name=value[2],
            registry_type=value[3],
            total_size=value[4],
        )

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class ModelReadmeInfo:
    """Individual model readme information"""

    model_id: str
    revision: str
    readme_content: str
    registry_type: ArtifactRegistryType
    registry_name: str


@dataclass
class ModelsReadmeFetchDoneEvent(BaseArtifactEvent):
    models: list[ModelReadmeInfo]

    @classmethod
    @override
    def event_name(cls) -> str:
        return "models_readme_fetch_done"

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
                )
                for model in self.models
            ),
        )

    @classmethod
    def deserialize(cls, value: tuple):
        return cls(
            models=[
                ModelReadmeInfo(
                    model_id=m[0],
                    revision=m[1],
                    readme_content=m[2],
                    registry_name=m[3],
                    registry_type=m[4],
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
