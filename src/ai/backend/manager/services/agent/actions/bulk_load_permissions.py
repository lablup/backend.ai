from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.agent import AgentUUID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction


@dataclass
class BulkLoadAgentPermissionsAction(BasePartialBulkAction):
    """Read the permissions the caller holds on each agent named."""

    agent_uuids: Sequence[AgentUUID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_load_agent_permissions"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.agent_uuids)

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, agent_uuids=[uuid for uuid in self.agent_uuids if uuid in allowed])
