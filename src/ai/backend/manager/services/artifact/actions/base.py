from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact import ARTIFACT_ENTITY_TYPE, ArtifactID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ArtifactAction(BaseGlobalAction):
    """Base for an operation that names no single artifact."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ARTIFACT_ENTITY_TYPE


@dataclass
class ArtifactScopeAction(ArtifactAction):
    """Base for a read that spans the installation."""


@dataclass
class ArtifactSingleEntityAction(BaseSingleEntityAction):
    """Base for an operation on one artifact."""

    artifact_id: ArtifactID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.artifact_id
