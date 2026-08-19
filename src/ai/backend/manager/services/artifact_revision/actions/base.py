from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact_revision import (
    ARTIFACT_REVISION_ENTITY_TYPE,
    ArtifactRevisionID,
)
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ArtifactRevisionAction(BaseGlobalAction):
    """Base for an operation that names no single artifact revision."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ARTIFACT_REVISION_ENTITY_TYPE


@dataclass
class ArtifactRevisionScopeAction(ArtifactRevisionAction):
    """Base for a read that spans the installation."""


@dataclass
class ArtifactRevisionSingleEntityAction(BaseSingleEntityAction):
    """Base for an operation on one artifact revision."""

    artifact_revision_id: ArtifactRevisionID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.artifact_revision_id
