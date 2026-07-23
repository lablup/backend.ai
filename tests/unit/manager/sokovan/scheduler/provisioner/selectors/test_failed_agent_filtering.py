"""Tests for failed agent deprioritization in agent selection.

When a session fails to start on an agent, that agent is recorded per session
(``ResourceGroupResource.failed_sessions_by_agent`` from Valkey). The trackers
carry those session IDs and the selector deprioritizes agents where the
current session already failed.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

import pytest

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_group import ResourceGroupID
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, SessionId
from ai.backend.manager.data.session.options import AgentSelectionPolicy
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.concentrated import (
    ConcentratedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.dispersed import (
    DispersedAgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.selector import (
    AgentSelectionCriteria,
    AgentSelector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import (
    AgentStateTracker,
    build_agent_trackers,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.types import ResourceRequirements
from ai.backend.manager.views.sokovan.agent import (
    AgentLimit,
    AgentMeta,
    AgentResource,
    ResourceGroupResource,
    SlotResource,
)
from ai.backend.manager.views.sokovan.workload import ResourceRequest

AGENT_A = AgentId("agent-a")
AGENT_B = AgentId("agent-b")
SESSION_ID = SessionId(uuid.uuid4())
NO_LIMIT = AgentLimit(max_container_count=None)


def _agent_meta(agent_id: str) -> AgentMeta:
    return AgentMeta(
        id=AgentId(agent_id),
        addr=f"{agent_id}:6001",
        architecture=ArchName("x86_64"),
        resources=AgentResource(
            slots={
                ResourceSlotName("cpu"): SlotResource(
                    capacity=Decimal("8"), reserved=Decimal(0), used=Decimal(0)
                ),
                ResourceSlotName("mem"): SlotResource(
                    capacity=Decimal("16384"), reserved=Decimal(0), used=Decimal(0)
                ),
            }
        ),
        container_count=0,
    )


def _trackers(
    failed_agents: Mapping[str, frozenset[SessionId]] | None = None,
) -> list[AgentStateTracker]:
    """Build trackers for agent-a/agent-b via the shared construction point."""
    resources = ResourceGroupResource(
        agents=[_agent_meta("agent-a"), _agent_meta("agent-b")],
        failed_sessions_by_agent={
            AgentId(agent_id): sessions for agent_id, sessions in (failed_agents or {}).items()
        },
    )
    return build_agent_trackers(resources)


def _criteria(
    designated_agent_ids: list[AgentId] | None = None,
) -> AgentSelectionCriteria:
    return AgentSelectionCriteria(
        session_id=SESSION_ID,
        resource_group_id=ResourceGroupID(uuid.UUID(int=0)),
        requirements=[
            ResourceRequirements(
                requested_slots=ResourceRequest(
                    slots={
                        ResourceSlotName("cpu"): Decimal("1"),
                        ResourceSlotName("mem"): Decimal("1024"),
                    }
                ),
                required_architecture=ArchName("x86_64"),
                container_count=1,
            )
        ],
        agent_selection_policy=AgentSelectionPolicy.STRICT,
        designated_agent_ids=designated_agent_ids,
    )


@pytest.fixture
def concentrated_selector() -> AgentSelector:
    return AgentSelector(ConcentratedAgentSelector(["cpu", "mem"]))


@pytest.fixture
def dispersed_selector() -> AgentSelector:
    return AgentSelector(DispersedAgentSelector(["cpu", "mem"]))


class TestFailedAgentFiltering:
    """Failed agents are deprioritized before the strategy runs."""

    async def test_failed_agent_is_avoided(
        self,
        concentrated_selector: AgentSelector,
    ) -> None:
        """An agent where this session previously failed is excluded."""
        trackers = _trackers({"agent-a": frozenset({SESSION_ID})})

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            trackers, _criteria(), NO_LIMIT
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AGENT_B

    async def test_other_sessions_failures_do_not_filter(
        self,
        concentrated_selector: AgentSelector,
    ) -> None:
        """Failures recorded for other sessions leave selection unchanged."""
        other_session = SessionId(uuid.uuid4())
        trackers = _trackers({
            "agent-a": frozenset({other_session}),
            "agent-b": frozenset({other_session}),
        })

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            trackers, _criteria(), NO_LIMIT
        )

        assert len(selections) == 1

    async def test_all_agents_failed_fallback(
        self,
        concentrated_selector: AgentSelector,
    ) -> None:
        """When every compatible agent has failed, the filter is skipped."""
        trackers = _trackers({
            "agent-a": frozenset({SESSION_ID}),
            "agent-b": frozenset({SESSION_ID}),
        })

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            trackers, _criteria(), NO_LIMIT
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id in {AGENT_A, AGENT_B}

    async def test_no_failed_agents_no_change(
        self,
        concentrated_selector: AgentSelector,
    ) -> None:
        """No prior failures: normal selection proceeds."""
        trackers = _trackers()

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            trackers, _criteria(), NO_LIMIT
        )

        assert len(selections) == 1

    async def test_designated_agent_overrides_failed_filter(
        self,
        concentrated_selector: AgentSelector,
    ) -> None:
        """The designated-agent check runs before the failed-agent filter."""
        trackers = _trackers({"agent-a": frozenset({SESSION_ID})})

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            trackers, _criteria(designated_agent_ids=[AGENT_A]), NO_LIMIT
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AGENT_A

    async def test_failed_filter_works_with_dispersed_strategy(
        self,
        dispersed_selector: AgentSelector,
    ) -> None:
        """Filtering happens upstream of the strategy, not inside it."""
        trackers = _trackers({"agent-a": frozenset({SESSION_ID})})

        selections = await dispersed_selector.select_agents_for_batch_requirements(
            trackers, _criteria(), NO_LIMIT
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id == AGENT_B

    async def test_failed_agent_not_in_pool_is_ignored(
        self,
        concentrated_selector: AgentSelector,
    ) -> None:
        """A failure record for an agent no longer in the pool is harmless."""
        trackers = _trackers({"agent-nonexistent": frozenset({SESSION_ID})})

        selections = await concentrated_selector.select_agents_for_batch_requirements(
            trackers, _criteria(), NO_LIMIT
        )

        assert len(selections) == 1
        assert selections[0].selected_agent.agent_id in {AGENT_A, AGENT_B}
