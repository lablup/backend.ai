from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.deployment import DeploymentID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.bulk.base import BasePartialBulkAction


@dataclass(frozen=True)
class BulkGetDeploymentDesignatedAgentsAction(BasePartialBulkAction):
    """Read the agents each named deployment designates.

    Answered for by each deployment the ids name.
    """

    deployment_ids: list[DeploymentID]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_deployment_designated_agents"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return self.deployment_ids

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self,
            deployment_ids=[did for did in self.deployment_ids if did in allowed],
        )
