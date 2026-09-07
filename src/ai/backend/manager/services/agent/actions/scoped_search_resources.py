"""Read of the slot rows the named agents carry."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.resource_slot.types import AgentResourceData
from ai.backend.manager.models.resource_slot.row import AgentResourceRow
from ai.backend.manager.models.resource_slot.scopes import AgentResourceOperationScope
from ai.backend.manager.models.resource_slot.searchers import AgentResourceSearcher
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class ScopedSearchAgentResourcesAction(
    BulkScopedSearchOpsAction[AgentResourceRow, AgentResourceData]
):
    """Read the slot rows of the agents named, combined with OR.

    Every agent is authorized before the read runs, so a caller reaching for one they
    cannot see is refused rather than served the rest.
    """

    agent_uuids: Sequence[AgentUUID]
    searcher: AgentResourceSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "scoped_search_agent_resources"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.agent_uuids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [AgentResourceOperationScope(agent_uuid=uuid) for uuid in self.agent_uuids]

    @override
    def to_searcher(self) -> AgentResourceSearcher:
        return self.searcher
