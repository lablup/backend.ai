from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AgentEntityType, AgentUUID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.v2.ops.base import BulkLookupEntityOpsAction
from ai.backend.manager.models.agent.lookups import AgentNamesLookup
from ai.backend.manager.services.agent.actions.lookup import AgentNameKey


@dataclass
class BulkLookupAgentsAction(BulkLookupEntityOpsAction[AgentId, AgentUUID]):
    """Resolve several operator-facing agent ids into the agents they name.

    Every authenticated caller may resolve the keys, as with the single lookup: the
    read that follows is checked against each agent on its own.
    """

    agent_ids: Sequence[AgentId]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AgentEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_lookup_agents"

    @override
    def keys(self) -> Sequence[AgentId]:
        return tuple(self.agent_ids)

    @override
    def to_lookup_key(self, key: AgentId) -> AgentNameKey:
        return AgentNameKey(agent_id=key)

    @override
    def to_lookup(self) -> AgentNamesLookup:
        return AgentNamesLookup()
