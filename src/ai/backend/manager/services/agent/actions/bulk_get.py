from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.models.agent.queriers import BulkAgentQuerier
from ai.backend.manager.models.agent.row import AgentRow


@dataclass
class BulkGetAgentsAction(PartialBulkGetEntityOpsAction[AgentRow, AgentData]):
    """Read the agents the caller named, answering for each id."""

    ids: Sequence[AgentUUID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_agents"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkAgentQuerier:
        return BulkAgentQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
