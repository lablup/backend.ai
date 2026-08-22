from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE, ModelCardID
from ai.backend.common.data.entity.model_card_resource_requirement import (
    ModelCardResourceRequirementID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.model_card.lookups import (
    ModelCardResourceRequirementOwnerLookup,
)


@dataclass(frozen=True)
class ModelCardResourceRequirementIDLookupKey(LookupKey):
    """A requirement row's id, resolved into the card that owns it."""

    requirement_id: ModelCardResourceRequirementID

    @override
    def kind(self) -> str:
        return "model_card_resource_requirement_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.requirement_id)}


@dataclass
class LookupModelCardResourceRequirementOwnerAction(
    LookupFieldOwnerOpsAction[ModelCardResourceRequirementID, ModelCardID]
):
    """The card a requirement row belongs to."""

    requirement_id: ModelCardResourceRequirementID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MODEL_CARD_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_model_card_resource_requirement_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return ModelCardResourceRequirementIDLookupKey(self.requirement_id)

    @override
    def field_id(self) -> ModelCardResourceRequirementID:
        return self.requirement_id

    @override
    def to_owner_lookup(self) -> ModelCardResourceRequirementOwnerLookup:
        return ModelCardResourceRequirementOwnerLookup()


@dataclass
class LookupBulkModelCardResourceRequirementOwnerAction(
    LookupBulkFieldOwnerOpsAction[ModelCardResourceRequirementID, ModelCardID]
):
    """The cards several requirement rows belong to."""

    requirement_ids: Sequence[ModelCardResourceRequirementID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MODEL_CARD_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_model_card_resource_requirement_owner"

    @override
    def to_lookup_key(self, field_id: ModelCardResourceRequirementID) -> LookupKey:
        return ModelCardResourceRequirementIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[ModelCardResourceRequirementID]:
        return tuple(self.requirement_ids)

    @override
    def to_owner_lookup(self) -> ModelCardResourceRequirementOwnerLookup:
        return ModelCardResourceRequirementOwnerLookup()
