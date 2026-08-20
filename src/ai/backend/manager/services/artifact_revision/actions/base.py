from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.common.data.entity.types import GLOBAL_ENTITY_TYPE, EntityType
from ai.backend.manager.actions.v2.field.base import BaseSingleFieldAction
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction
from ai.backend.manager.services.artifact_revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
)


@dataclass
class ArtifactRevisionAction(BaseGlobalAction):
    """Base for an operation that names no single artifact revision."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GLOBAL_ENTITY_TYPE


@dataclass
class ArtifactRevisionScopeAction(ArtifactRevisionAction):
    """Base for a read that spans the installation."""


@dataclass
class ArtifactRevisionSingleEntityAction(BaseSingleFieldAction[ArtifactRevisionID, ArtifactID]):
    """Base for an operation on one artifact revision.

    A revision is a field of the artifact it belongs to, so the artifact answers for it
    and is read by the lookup this names.
    """

    artifact_revision_id: ArtifactRevisionID

    @override
    def to_owner_lookup_action(self) -> LookupArtifactRevisionOwnerAction:
        return LookupArtifactRevisionOwnerAction(revision_id=self.artifact_revision_id)
