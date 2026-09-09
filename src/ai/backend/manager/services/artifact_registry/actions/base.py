from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact_registry import (
    ArtifactRegistryEntityType,
    ArtifactRegistryID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ArtifactRegistryAction(BaseGlobalAction):
    """Base for an operation that names no single artifact registry."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ArtifactRegistryEntityType()


@dataclass
class ArtifactRegistryScopeAction(ArtifactRegistryAction):
    """Base for a read that spans the installation."""


@dataclass
class ArtifactRegistrySingleEntityAction(BaseSingleEntityAction):
    """Base for an operation on one artifact registry."""

    registry_id: ArtifactRegistryID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.registry_id
