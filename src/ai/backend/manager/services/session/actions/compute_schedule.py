from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.types import AgentId, ClusterMode
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.session.compute_schedule import (
    ComputeScheduleResult,
)
from ai.backend.manager.data.session.draft import KernelResourceInput
from ai.backend.manager.data.session.options import AgentSelectionPolicy


@dataclass(frozen=True)
class ComputeScheduleAction(BaseSingleEntityAction):
    """Compute a session's scheduling against a resource group without provisioning.

    The answer describes the named group's nodes -- which kernels fit and how much
    to subtract for the ones that do not -- so the read is answered for that group,
    not for the session that does not exist yet. Read on the resource group is the
    gate; ``DOMAIN/PROJECT/USER -> RESOURCE_GROUP`` is a scope-entity edge, so a
    caller reaches the group through the scope it is bound to.

    The fields mirror the scheduler's selection criteria so the real selector can
    be driven directly: ``cluster_mode`` decides whether kernel slots are summed
    onto a single node (SINGLE_NODE) or placed individually (MULTI_NODE).

    Each kernel is an unresolved ``KernelResourceInput``; the result list
    corresponds positionally, so callers match results to kernels by index.
    """

    kernels: list[KernelResourceInput]
    cluster_mode: ClusterMode
    resource_group_id: ResourceGroupID
    designated_agent_ids: list[AgentId] | None
    agent_selection_policy: AgentSelectionPolicy | None

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.resource_group_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "compute_schedule"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class ComputeScheduleActionResult:
    result: ComputeScheduleResult
