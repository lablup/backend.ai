from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.agent import AgentEntityType, AgentUUID
from ai.backend.common.data.entity.agent_resource import AgentResourceID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.field.bulk_lookup import LookupBulkFieldOwnerOpsAction
from ai.backend.manager.actions.v2.field.lookup import LookupFieldOwnerOpsAction
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.models.resource_slot.lookups import AgentResourceOwnerLookup


@dataclass(frozen=True)
class AgentResourceIDLookupKey(LookupKey):
    """A slot row's id, resolved into the agent that owns it."""

    resource_id: AgentResourceID

    @override
    def kind(self) -> str:
        return "agent_resource_id"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.resource_id)}


@dataclass
class LookupAgentResourceOwnerAction(LookupFieldOwnerOpsAction[AgentResourceID, AgentUUID]):
    """The agent a slot row belongs to."""

    resource_id: AgentResourceID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AgentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_agent_resource_owner"

    @override
    def lookup_key(self) -> LookupKey:
        return AgentResourceIDLookupKey(self.resource_id)

    @override
    def field_id(self) -> AgentResourceID:
        return self.resource_id

    @override
    def to_owner_lookup(self) -> AgentResourceOwnerLookup:
        return AgentResourceOwnerLookup()


@dataclass
class LookupBulkAgentResourceOwnerAction(LookupBulkFieldOwnerOpsAction[AgentResourceID, AgentUUID]):
    """The agents several slot rows belong to."""

    resource_ids: Sequence[AgentResourceID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AgentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_bulk_agent_resource_owner"

    @override
    def to_lookup_key(self, field_id: AgentResourceID) -> LookupKey:
        return AgentResourceIDLookupKey(field_id)

    @override
    def field_ids(self) -> Sequence[AgentResourceID]:
        return tuple(self.resource_ids)

    @override
    def to_owner_lookup(self) -> AgentResourceOwnerLookup:
        return AgentResourceOwnerLookup()
