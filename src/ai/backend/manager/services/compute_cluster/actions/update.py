from __future__ import annotations

from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.models.compute_cluster.updaters import ComputeClusterUpdater
from ai.backend.manager.types import OptionalState


@dataclass(frozen=True)
class UpdateComputeClusterAction(BaseSingleEntityAction):
    """Change a compute cluster. ``kubeconfig`` is plaintext; the service encrypts it into
    the updater, whose own ``kubeconfig`` is left as a no-op."""

    updater: ComputeClusterUpdater
    kubeconfig: OptionalState[str] = field(default_factory=OptionalState[str].nop, repr=False)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_compute_cluster"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.compute_cluster_id
