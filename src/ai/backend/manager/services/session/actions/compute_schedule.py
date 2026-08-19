from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.types import AgentId, ClusterMode
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.compute_schedule import (
    ComputeScheduleResult,
)
from ai.backend.manager.data.session.draft import KernelResourceInput
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.services.session.base import SessionGlobalAction


@dataclass(frozen=True)
class ComputeScheduleAction(SessionGlobalAction):
    """Compute a session's scheduling against a resource group without provisioning.

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
    @classmethod
    def action_name(cls) -> str:
        return "global_compute_schedule"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass(frozen=True)
class ComputeScheduleActionResult:
    result: ComputeScheduleResult
