from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.common.data.entity.types import (
    GLOBAL_ENTITY_TYPE,
    EntityType,
)
from ai.backend.manager.actions.v2.field.bulk_lookup import (
    LookupBulkRuntimeFieldOwnerOpsAction,
)
from ai.backend.manager.actions.v2.field.lookup import LookupRuntimeFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.entity_label.lookups import EntityLabelOwnerLookup


@dataclass(frozen=True)
class EntityLabelIDLookupKey(LookupKey):
    """A label's id, resolved into the entity it is on."""

    label_id: EntityLabelID

    @override
    def kind(self) -> str:
        return "entity_label_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.label_id)}


@dataclass
class LookupEntityLabelOwnerAction(LookupRuntimeFieldOwnerOpsAction[EntityLabelID]):
    """The entity one label is on.

    ``entity_type`` names no kind: a label goes on any of them, and this read is what
    finds out which. It records the run rather than gating it — the operation that
    follows is authorized against the entity this answers with.
    """

    label_id: EntityLabelID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GLOBAL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_entity_label_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return EntityLabelIDLookupKey(self.label_id)

    @override
    def field_id(self) -> EntityLabelID:
        return self.label_id

    @override
    def to_owner_lookup(self) -> EntityLabelOwnerLookup:
        return EntityLabelOwnerLookup()


@dataclass
class LookupBulkEntityLabelOwnerAction(LookupBulkRuntimeFieldOwnerOpsAction[EntityLabelID]):
    """The entities several labels are on."""

    label_ids: Sequence[EntityLabelID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GLOBAL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_entity_label_owner"

    @override
    def to_lookup_key(self, field_id: EntityLabelID) -> LookupKey:
        return EntityLabelIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[EntityLabelID]:
        return tuple(self.label_ids)

    @override
    def to_owner_lookup(self) -> EntityLabelOwnerLookup:
        return EntityLabelOwnerLookup()
