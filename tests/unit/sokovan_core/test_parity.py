"""Parity between the manager's agent selection entry point and the core API.

The manager path builds the selector with its recorder and converts a
`SessionWorkload`; the core path feeds `AgentSelectionCriteria` directly.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal

import pytest

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.exception import BackendAIError
from ai.backend.common.types import (
    AccessKey,
    AgentId,
    AgentSelectionStrategy,
    ArchName,
    ClusterMode,
    KernelId,
    PreemptionOrder,
    SessionId,
    SessionTypes,
)
from ai.backend.manager.sokovan.recorder.context import RecorderContext
from ai.backend.manager.sokovan.scheduler.provisioner.selection import (
    create_agent_selector as create_manager_selector,
)
from ai.backend.manager.sokovan.scheduler.provisioner.selection import (
    selection_criteria_from_workload,
)
from ai.backend.manager.views.sokovan.workload import (
    SessionWorkload,
    WorkloadMeta,
    WorkloadOwner,
)
from ai.backend.sokovan_core.selectors.pool import create_agent_selector as create_core_selector
from ai.backend.sokovan_core.selectors.selector import AgentSelectionCriteria, PlacementPlan
from ai.backend.sokovan_core.selectors.tracker import AgentStateTracker, build_agent_trackers
from ai.backend.sokovan_core.types.agent import (
    AgentLimit,
    AgentMeta,
    AgentResource,
    ResourceGroupResource,
    SlotResource,
)
from ai.backend.sokovan_core.types.policy import (
    AgentSelectionPolicy,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.sokovan_core.types.workload import (
    KernelWorkload,
    ResourceRequest,
    SessionGroupPolicy,
    SessionPlacement,
)

RESOURCE_GROUP_ID = ResourceGroupID(uuid.UUID(int=0))
GROUP_ID = SessionGroupID(uuid.UUID(int=7))


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    cpu_capacity: str = "16"
    cpu_used: str = "0"
    mem_capacity: str = "32768"
    architecture: str = "x86_64"
    container_count: int = 0


@dataclass(frozen=True)
class SessionSpec:
    kernel_slots: Sequence[Mapping[str, str]]
    cluster_mode: ClusterMode = ClusterMode.SINGLE_NODE
    architecture: str = "x86_64"
    designated: Sequence[str] | None = None
    agent_selection_policy: AgentSelectionPolicy = AgentSelectionPolicy.STRICT
    session_group: SessionGroupPolicy | None = None


@dataclass(frozen=True)
class Scenario:
    strategy: AgentSelectionStrategy
    agents: Sequence[AgentSpec]
    sessions: Sequence[SessionSpec]
    # The outcome of each session, in order: chosen agent ids or the error type name
    expected: Sequence[tuple[str, ...] | str]
    max_container_count: int | None = None
    group_members: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class Placed:
    agent_ids: tuple[str, ...]


@dataclass(frozen=True)
class Failed:
    error_type: str
    message: str
    error_code: str


type Outcome = Placed | Failed


def _agent_meta(spec: AgentSpec) -> AgentMeta:
    return AgentMeta(
        id=AgentId(spec.agent_id),
        addr=f"{spec.agent_id}:6001",
        architecture=ArchName(spec.architecture),
        resources=AgentResource(
            slots={
                ResourceSlotName("cpu"): SlotResource(
                    capacity=Decimal(spec.cpu_capacity),
                    reserved=Decimal(0),
                    used=Decimal(spec.cpu_used),
                ),
                ResourceSlotName("mem"): SlotResource(
                    capacity=Decimal(spec.mem_capacity),
                    reserved=Decimal(0),
                    used=Decimal(0),
                ),
            }
        ),
        container_count=spec.container_count,
    )


def _trackers(scenario: Scenario) -> list[AgentStateTracker]:
    return build_agent_trackers(
        ResourceGroupResource(
            agents=[_agent_meta(spec) for spec in scenario.agents],
            group_members_by_agent={
                AgentId(agent_id): {GROUP_ID: count}
                for agent_id, count in scenario.group_members.items()
            },
        )
    )


def _workload(spec: SessionSpec, session_id: SessionId) -> SessionWorkload:
    return SessionWorkload(
        meta=WorkloadMeta(
            session_id=session_id,
            resource_group_id=RESOURCE_GROUP_ID,
            owner=WorkloadOwner(
                access_key=AccessKey("AKTEST"),
                user_uuid=UserID(uuid.UUID(int=3)),
                project_id=ProjectID(uuid.UUID(int=1)),
                domain_id=DomainID(uuid.UUID(int=2)),
            ),
        ),
        placement=SessionPlacement(
            cluster_mode=spec.cluster_mode,
            kernels=[
                KernelWorkload(
                    kernel_id=KernelId(uuid.UUID(int=100 + index)),
                    architecture=ArchName(spec.architecture),
                    requested_slots=ResourceRequest(
                        slots={
                            ResourceSlotName(name): Decimal(amount)
                            for name, amount in slots.items()
                        }
                    ),
                )
                for index, slots in enumerate(spec.kernel_slots)
            ],
            agent_selection_policy=spec.agent_selection_policy,
            designated_agent_ids=(
                [AgentId(agent_id) for agent_id in spec.designated]
                if spec.designated is not None
                else None
            ),
            session_group=spec.session_group,
        ),
        priority=0,
        job_priority=0,
        session_type=SessionTypes.INTERACTIVE,
        requested_starts_at=None,
        is_preemptible=False,
    )


def _failed(error: BackendAIError) -> Failed:
    return Failed(
        error_type=type(error).__name__,
        message=str(error),
        error_code=str(error.error_code()),
    )


async def _run_manager(scenario: Scenario, session_ids: Sequence[SessionId]) -> list[Outcome]:
    """Run through the manager entry point inside a recording scope."""
    selector = create_manager_selector(["cpu", "mem"])
    trackers = _trackers(scenario)
    limit = AgentLimit(max_container_count=scenario.max_container_count)
    outcomes: list[Outcome] = []
    with RecorderContext[SessionId].scope("parity", entity_ids=list(session_ids)) as pool:
        for spec, session_id in zip(scenario.sessions, session_ids, strict=True):
            workload = _workload(spec, session_id)
            plan = PlacementPlan.from_placement(workload.placement)
            criteria = selection_criteria_from_workload(workload, plan, None)
            with pool.recorder(session_id).phase("select"):
                try:
                    selections = await selector.select_agents_for_batch_requirements(
                        scenario.strategy, trackers, criteria, limit, PreemptionOrder.OLDEST
                    )
                except BackendAIError as e:
                    outcomes.append(_failed(e))
                    continue
            outcomes.append(Placed(tuple(s.selected_agent.agent_id for s in selections)))
    return outcomes


async def _run_core(scenario: Scenario, session_ids: Sequence[SessionId]) -> list[Outcome]:
    """Run through the core API with the selection input built directly."""
    selector = create_core_selector(["cpu", "mem"])
    trackers = _trackers(scenario)
    limit = AgentLimit(max_container_count=scenario.max_container_count)
    outcomes: list[Outcome] = []
    for spec, session_id in zip(scenario.sessions, session_ids, strict=True):
        placement = _workload(spec, session_id).placement
        plan = PlacementPlan.from_placement(placement)
        criteria = AgentSelectionCriteria(
            session_id=session_id,
            resource_group_id=RESOURCE_GROUP_ID,
            requirements=plan.requirements(),
            agent_selection_policy=placement.agent_selection_policy,
            designated_agent_ids=placement.designated_agent_ids,
            job_priority=0,
            victim_candidates=None,
            session_group=placement.session_group,
        )
        try:
            selections = await selector.select_agents_for_batch_requirements(
                scenario.strategy, trackers, criteria, limit, PreemptionOrder.OLDEST
            )
        except BackendAIError as e:
            outcomes.append(_failed(e))
            continue
        outcomes.append(Placed(tuple(s.selected_agent.agent_id for s in selections)))
    return outcomes


_SMALL = {"cpu": "2", "mem": "1024"}
_BUSY_AND_IDLE = (AgentSpec("a1", cpu_used="12"), AgentSpec("a2"))

SCENARIOS: dict[str, Scenario] = {
    "concentrated-single-node": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=_BUSY_AND_IDLE,
        sessions=[SessionSpec(kernel_slots=[_SMALL, _SMALL])],
        expected=[("a1",)],
    ),
    "dispersed-single-node": Scenario(
        strategy=AgentSelectionStrategy.DISPERSED,
        agents=_BUSY_AND_IDLE,
        sessions=[SessionSpec(kernel_slots=[_SMALL, _SMALL])],
        expected=[("a2",)],
    ),
    "roundrobin-across-sessions": Scenario(
        strategy=AgentSelectionStrategy.ROUNDROBIN,
        agents=(AgentSpec("a1"), AgentSpec("a2"), AgentSpec("a3")),
        sessions=[SessionSpec(kernel_slots=[_SMALL]) for _ in range(4)],
        expected=[("a1",), ("a2",), ("a3",), ("a1",)],
    ),
    "dispersed-multi-node": Scenario(
        strategy=AgentSelectionStrategy.DISPERSED,
        agents=(AgentSpec("a1"), AgentSpec("a2")),
        sessions=[
            SessionSpec(
                kernel_slots=[{"cpu": "10", "mem": "1024"}] * 2,
                cluster_mode=ClusterMode.MULTI_NODE,
            )
        ],
        expected=[("a1", "a2")],
    ),
    "concentrated-commits-across-sessions": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=(AgentSpec("a1", cpu_capacity="4"), AgentSpec("a2", cpu_capacity="8")),
        sessions=[
            SessionSpec(kernel_slots=[{"cpu": "3", "mem": "1024"}]),
            SessionSpec(kernel_slots=[{"cpu": "3", "mem": "1024"}]),
        ],
        expected=[("a1",), ("a2",)],
    ),
    "designated-strict": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=_BUSY_AND_IDLE,
        sessions=[SessionSpec(kernel_slots=[_SMALL], designated=["a2"])],
        expected=[("a2",)],
    ),
    "designated-strict-absent": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=_BUSY_AND_IDLE,
        sessions=[SessionSpec(kernel_slots=[_SMALL], designated=["a9"])],
        expected=["NoCompatibleAgentError"],
    ),
    "designated-preferred-full-falls-back": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=(AgentSpec("a1", cpu_used="16"), AgentSpec("a2")),
        sessions=[
            SessionSpec(
                kernel_slots=[_SMALL],
                designated=["a1"],
                agent_selection_policy=AgentSelectionPolicy.PREFERRED,
            )
        ],
        expected=[("a2",)],
    ),
    "architecture-filter": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=(AgentSpec("a1", cpu_used="12"), AgentSpec("a2", architecture="aarch64")),
        sessions=[SessionSpec(kernel_slots=[_SMALL], architecture="aarch64")],
        expected=[("a2",)],
    ),
    "architecture-none-compatible": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=_BUSY_AND_IDLE,
        sessions=[SessionSpec(kernel_slots=[_SMALL], architecture="aarch64")],
        expected=["NoCompatibleAgentError"],
    ),
    "container-limit": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=(AgentSpec("a1", cpu_used="12", container_count=2), AgentSpec("a2")),
        sessions=[SessionSpec(kernel_slots=[_SMALL])],
        expected=[("a2",)],
        max_container_count=2,
    ),
    "container-limit-everywhere": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=(AgentSpec("a1", container_count=2), AgentSpec("a2", container_count=3)),
        sessions=[SessionSpec(kernel_slots=[_SMALL])],
        expected=["BatchAgentSelectionFailedError"],
        max_container_count=2,
    ),
    "insufficient-resources": Scenario(
        strategy=AgentSelectionStrategy.DISPERSED,
        agents=_BUSY_AND_IDLE,
        sessions=[SessionSpec(kernel_slots=[{"cpu": "32", "mem": "1024"}])],
        expected=["BatchAgentSelectionFailedError"],
    ),
    "insufficient-resources-multi-node-partial": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=_BUSY_AND_IDLE,
        sessions=[
            SessionSpec(
                kernel_slots=[_SMALL, {"cpu": "20", "mem": "1024"}],
                cluster_mode=ClusterMode.MULTI_NODE,
            ),
            SessionSpec(kernel_slots=[{"cpu": "4", "mem": "1024"}]),
        ],
        # The failed session rolls back, so the next one still fits on a1
        expected=["BatchAgentSelectionFailedError", ("a1",)],
    ),
    "no-agents": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=(),
        sessions=[SessionSpec(kernel_slots=[_SMALL])],
        expected=["NoAgentsInResourceGroupError"],
    ),
    "session-group-pack-preferred": Scenario(
        strategy=AgentSelectionStrategy.DISPERSED,
        agents=(AgentSpec("a1", cpu_used="8"), AgentSpec("a2")),
        group_members={"a1": 1},
        sessions=[
            SessionSpec(
                kernel_slots=[_SMALL],
                session_group=SessionGroupPolicy(
                    group_id=GROUP_ID,
                    direction=SessionGroupPlacementDirection.PACK,
                    enforcement=SessionGroupPlacementEnforcement.PREFERRED,
                ),
            )
        ],
        expected=[("a1",)],
    ),
    "session-group-spread-strict": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=(AgentSpec("a1", cpu_used="12"), AgentSpec("a2")),
        group_members={"a1": 1},
        sessions=[
            SessionSpec(
                kernel_slots=[_SMALL],
                session_group=SessionGroupPolicy(
                    group_id=GROUP_ID,
                    direction=SessionGroupPlacementDirection.SPREAD,
                    enforcement=SessionGroupPlacementEnforcement.STRICT,
                ),
            )
        ],
        expected=[("a2",)],
    ),
    "session-group-spread-strict-exhausted": Scenario(
        strategy=AgentSelectionStrategy.CONCENTRATED,
        agents=(AgentSpec("a1"),),
        group_members={"a1": 1},
        sessions=[
            SessionSpec(
                kernel_slots=[_SMALL],
                session_group=SessionGroupPolicy(
                    group_id=GROUP_ID,
                    direction=SessionGroupPlacementDirection.SPREAD,
                    enforcement=SessionGroupPlacementEnforcement.STRICT,
                ),
            )
        ],
        expected=["NoCompatibleAgentError"],
    ),
}


def _summary(outcome: Outcome) -> tuple[str, ...] | str:
    match outcome:
        case Placed(agent_ids=agent_ids):
            return agent_ids
        case Failed(error_type=error_type):
            return error_type


class TestManagerCoreParity:
    @pytest.mark.parametrize("scenario", SCENARIOS.values(), ids=SCENARIOS.keys())
    async def test_same_agents_and_errors(self, scenario: Scenario) -> None:
        session_ids = [SessionId(uuid.UUID(int=1000 + i)) for i in range(len(scenario.sessions))]

        manager_outcomes = await _run_manager(scenario, session_ids)
        core_outcomes = await _run_core(scenario, session_ids)

        assert manager_outcomes == core_outcomes
        assert [_summary(outcome) for outcome in core_outcomes] == list(scenario.expected)


class TestManagerRecording:
    async def test_manager_selector_records_filter_steps(self) -> None:
        session_id = SessionId(uuid.UUID(int=1000))
        scenario = SCENARIOS["concentrated-single-node"]
        workload = _workload(scenario.sessions[0], session_id)
        plan = PlacementPlan.from_placement(workload.placement)
        criteria = selection_criteria_from_workload(workload, plan, None)

        with RecorderContext[SessionId].scope("parity", entity_ids=[session_id]) as pool:
            with pool.recorder(session_id).phase("select"):
                await create_manager_selector(["cpu", "mem"]).select_agents_for_batch_requirements(
                    scenario.strategy,
                    _trackers(scenario),
                    criteria,
                    AgentLimit(max_container_count=None),
                    PreemptionOrder.OLDEST,
                )
            records = pool.build_all_records()

        steps = [step.name for step in records[session_id].phases[0].steps]
        assert steps == [
            "architecture",
            "designated-strict",
            "session-group-strict",
            "resource",
            "container-limit",
        ]
