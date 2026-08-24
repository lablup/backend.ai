from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.label import LabelID
from ai.backend.common.data.entity.types import (
    GLOBAL_ENTITY_TYPE,
    EntityType,
    RuntimeEntityID,
)
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.label.lookups import LabelOwnerLookup


@dataclass(frozen=True)
class LabelIDLookupKey(LookupKey):
    """A label's id, resolved into the entity it is on."""

    label_id: LabelID

    @override
    def kind(self) -> str:
        return "label_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.label_id)}


@dataclass
class LookupLabelOwnerAction(LookupFieldOwnerOpsAction[LabelID, RuntimeEntityID]):
    """The entity one label is on.

    ``entity_type`` names no kind: a label goes on any of them, and this read is what
    finds out which. It records the run rather than gating it — the operation that
    follows is authorized against the entity this answers with.
    """

    label_id: LabelID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GLOBAL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_label_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return LabelIDLookupKey(self.label_id)

    @override
    def field_id(self) -> LabelID:
        return self.label_id

    @override
    def to_owner_lookup(self) -> LabelOwnerLookup:
        return LabelOwnerLookup()


@dataclass
class LookupBulkLabelOwnerAction(LookupBulkFieldOwnerOpsAction[LabelID, RuntimeEntityID]):
    """The entities several labels are on."""

    label_ids: Sequence[LabelID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return GLOBAL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_label_owner"

    @override
    def to_lookup_key(self, field_id: LabelID) -> LookupKey:
        return LabelIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[LabelID]:
        return tuple(self.label_ids)

    @override
    def to_owner_lookup(self) -> LabelOwnerLookup:
        return LabelOwnerLookup()
