from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.artifact import ARTIFACT_ENTITY_TYPE, ArtifactID
from ai.backend.common.data.entity.artifact_revision import ArtifactRevisionID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.artifact_revision.lookups import ArtifactRevisionOwnerLookup


@dataclass(frozen=True)
class ArtifactRevisionIDLookupKey(LookupKey):
    """A revision's id, resolved into the artifact it belongs to."""

    revision_id: ArtifactRevisionID

    @override
    def kind(self) -> str:
        return "artifact_revision_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.revision_id)}


@dataclass
class LookupArtifactRevisionOwnerAction(LookupFieldOwnerOpsAction[ArtifactRevisionID, ArtifactID]):
    """The artifact a revision belongs to."""

    revision_id: ArtifactRevisionID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ARTIFACT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_artifact_revision_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return ArtifactRevisionIDLookupKey(self.revision_id)

    @override
    def field_id(self) -> ArtifactRevisionID:
        return self.revision_id

    @override
    def to_owner_lookup(self) -> ArtifactRevisionOwnerLookup:
        return ArtifactRevisionOwnerLookup()


@dataclass
class LookupBulkArtifactRevisionOwnerAction(
    LookupBulkFieldOwnerOpsAction[ArtifactRevisionID, ArtifactID]
):
    """The artifacts several revisions belong to."""

    revision_ids: Sequence[ArtifactRevisionID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ARTIFACT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_artifact_revision_owner"

    @override
    def to_lookup_key(self, field_id: ArtifactRevisionID) -> LookupKey:
        return ArtifactRevisionIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[ArtifactRevisionID]:
        return tuple(self.revision_ids)

    @override
    def to_owner_lookup(self) -> ArtifactRevisionOwnerLookup:
        return ArtifactRevisionOwnerLookup()
