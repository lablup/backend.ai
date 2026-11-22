"""Manager boundary of the `sokovan_core` agent selection.

Builds the selector with the manager's recorder and converts a session
workload into the selection input; no other manager module does either.
"""

from __future__ import annotations

from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.recorder.recorder import TransitionRecorder
from ai.backend.manager.views.sokovan.workload import SessionWorkload
from ai.backend.sokovan_core.selectors.pool import create_agent_selector as create_core_selector
from ai.backend.sokovan_core.selectors.selector import (
    AgentSelectionCriteria,
    AgentSelector,
    PlacementPlan,
)
from ai.backend.sokovan_core.types.preemption import ScopeVictimCandidates


class RecorderContextProvider:
    """Hands the selector the recorder of the active `RecorderContext` scope."""

    def recorder_for(self, session_id: SessionId) -> TransitionRecorder[SessionId] | None:
        try:
            pool = RecorderContext[SessionId].current_pool()
        except LookupError:
            return None
        return pool.recorder(session_id)


def create_agent_selector(agent_selection_resource_priority: list[str]) -> AgentSelector:
    """The shared selector, recording its filter steps into the scheduling history."""
    return create_core_selector(
        agent_selection_resource_priority,
        recorder_provider=RecorderContextProvider(),
    )


def selection_criteria_from_workload(
    workload: SessionWorkload,
    plan: PlacementPlan,
    victim_candidates: ScopeVictimCandidates | None,
) -> AgentSelectionCriteria:
    """Project a session workload (and its grouped plan) into the selection input."""
    return AgentSelectionCriteria(
        session_id=workload.meta.session_id,
        resource_group_id=workload.meta.resource_group_id,
        requirements=plan.requirements(),
        agent_selection_policy=workload.placement.agent_selection_policy,
        designated_agent_ids=workload.placement.designated_agent_ids,
        job_priority=workload.job_priority,
        victim_candidates=victim_candidates,
        session_group=workload.placement.session_group,
    )
