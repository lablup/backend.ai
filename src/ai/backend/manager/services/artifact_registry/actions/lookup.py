from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.artifact_registry import (
    ARTIFACT_REGISTRY_ENTITY_TYPE,
    ArtifactRegistryID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.models.artifact_registries.lookups import ArtifactRegistryNameLookup
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow


@dataclass(frozen=True)
class ArtifactRegistryNameKey(LookupKey):
    """The name a caller passes instead of the registry's id."""

    name: str

    @override
    def kind(self) -> str:
        return "artifact_registry_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}


@dataclass
class LookupArtifactRegistryAction(LookupEntityOpsAction[ArtifactRegistryRow, ArtifactRegistryID]):
    """Resolve an artifact registry's name into the registry it names."""

    name: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ARTIFACT_REGISTRY_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_artifact_registry"

    @override
    def lookup_key(self) -> ArtifactRegistryNameKey:
        return ArtifactRegistryNameKey(name=self.name)

    @override
    def to_lookup(self) -> ArtifactRegistryNameLookup:
        return ArtifactRegistryNameLookup(name=self.name)
