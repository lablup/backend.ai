from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE, AgentUUID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.v2.lookup.base import LookupKey
from ai.backend.manager.actions.v2.ops.base import LookupEntityOpsAction
from ai.backend.manager.models.agent.lookups import AgentNameLookup
from ai.backend.manager.models.agent.row import AgentRow


@dataclass(frozen=True)
class AgentNameKey(LookupKey):
    """The operator-facing id a caller passes instead of the agent's uuid."""

    agent_id: AgentId

    @override
    def kind(self) -> str:
        return "agent_name"

    @override
    def to_dict(self) -> dict[str, Any]:
        return {"agent_id": str(self.agent_id)}


@dataclass
class LookupAgentAction(LookupEntityOpsAction[AgentRow, AgentUUID]):
    """Resolve the operator-facing agent id into the agent it names."""

    agent_id: AgentId

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return AGENT_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "lookup_agent"

    @override
    def lookup_key(self) -> AgentNameKey:
        return AgentNameKey(agent_id=self.agent_id)

    @override
    def to_lookup(self) -> AgentNameLookup:
        return AgentNameLookup(agent_id=self.agent_id)
