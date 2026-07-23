"""Tests for AgentStateTracker and build_agent_trackers."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from decimal import Decimal

from ai.backend.common.identifier.architecture import ArchName
from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import AgentId, SessionId
from ai.backend.manager.sokovan.scheduler.provisioner.selectors.tracker import (
    AgentStateTracker,
    build_agent_trackers,
)
from ai.backend.manager.views.sokovan.agent import (
    AgentInfo,
    AgentMeta,
    AgentResource,
    ResourceGroupResource,
    SlotResource,
)
from ai.backend.manager.views.sokovan.workload import ResourceRequest

CPU = ResourceSlotName("cpu")
MEM = ResourceSlotName("mem")


def _agent_info(
    capacities: Mapping[str, str],
    reserved: Mapping[str, str] | None = None,
    used: Mapping[str, str] | None = None,
    container_count: int = 0,
) -> AgentInfo:
    reserved = reserved or {}
    used = used or {}
    return AgentInfo(
        agent_id=AgentId("agent-x"),
        agent_addr="agent-x:6001",
        architecture=ArchName("x86_64"),
        resources=AgentResource(
            slots={
                ResourceSlotName(name): SlotResource(
                    capacity=Decimal(amount),
                    reserved=Decimal(reserved.get(name, "0")),
                    used=Decimal(used.get(name, "0")),
                )
                for name, amount in capacities.items()
            }
        ),
        container_count=container_count,
    )


def _request(slots: Mapping[str, str]) -> ResourceRequest:
    return ResourceRequest(
        slots={ResourceSlotName(name): Decimal(amount) for name, amount in slots.items()}
    )


class TestAgentStateTracker:
    def test_remaining_slots_subtracts_reserved_and_used(self) -> None:
        tracker = AgentStateTracker(
            original_agent=_agent_info(
                {"cpu": "8", "mem": "16384"},
                reserved={"cpu": "1"},
                used={"cpu": "2", "mem": "4096"},
            )
        )

        remaining = tracker.remaining_slots()
        assert remaining[CPU] == Decimal("5")
        assert remaining[MEM] == Decimal("12288")

    def test_apply_diff_tracks_pending_allocation(self) -> None:
        tracker = AgentStateTracker(original_agent=_agent_info({"cpu": "8"}))

        tracker.apply_diff(_request({"cpu": "3"}), containers=2)

        assert tracker.remaining_slots()[CPU] == Decimal("5")
        assert tracker.current_container_count() == 2
        assert tracker.pending_containers == 2

    def test_commit_folds_pending_into_committed(self) -> None:
        tracker = AgentStateTracker(original_agent=_agent_info({"cpu": "8"}))
        tracker.apply_diff(_request({"cpu": "3"}), containers=1)

        tracker.commit()

        assert tracker.committed_slots[CPU] == Decimal("3")
        assert tracker.committed_containers == 1
        assert tracker.pending_slots == {}
        assert tracker.pending_containers == 0
        # Remaining still reflects the committed allocation
        assert tracker.remaining_slots()[CPU] == Decimal("5")

    def test_rollback_discards_pending_only(self) -> None:
        tracker = AgentStateTracker(original_agent=_agent_info({"cpu": "8"}))
        tracker.apply_diff(_request({"cpu": "2"}), containers=1)
        tracker.commit()
        tracker.apply_diff(_request({"cpu": "4"}), containers=1)

        tracker.rollback()

        assert tracker.remaining_slots()[CPU] == Decimal("6")
        assert tracker.committed_slots[CPU] == Decimal("2")
        assert tracker.pending_slots == {}

    def test_container_count_includes_base_count(self) -> None:
        tracker = AgentStateTracker(original_agent=_agent_info({"cpu": "8"}, container_count=3))
        tracker.apply_diff(_request({"cpu": "1"}), containers=1)
        tracker.commit()
        tracker.apply_diff(_request({"cpu": "1"}), containers=1)

        assert tracker.current_container_count() == 5


class TestBuildAgentTrackers:
    def test_builds_one_tracker_per_agent_with_failed_sessions(self) -> None:
        session_id = SessionId(uuid.uuid4())
        resources = ResourceGroupResource(
            agents=[
                AgentMeta(
                    id=AgentId("agent-a"),
                    addr="agent-a:6001",
                    architecture=ArchName("x86_64"),
                    resources=AgentResource(
                        slots={
                            CPU: SlotResource(
                                capacity=Decimal("8"),
                                reserved=Decimal(0),
                                used=Decimal(0),
                            )
                        }
                    ),
                    container_count=1,
                ),
                AgentMeta(
                    id=AgentId("agent-b"),
                    addr="agent-b:6001",
                    architecture=ArchName("aarch64"),
                    resources=AgentResource(slots={}),
                    container_count=0,
                ),
            ],
            failed_sessions_by_agent={AgentId("agent-a"): frozenset({session_id})},
        )

        trackers = build_agent_trackers(resources)

        assert len(trackers) == 2
        by_id = {tracker.original_agent.agent_id: tracker for tracker in trackers}
        assert by_id[AgentId("agent-a")].failed_session_ids == frozenset({session_id})
        assert by_id[AgentId("agent-b")].failed_session_ids == frozenset()
        assert by_id[AgentId("agent-a")].original_agent.container_count == 1
        assert by_id[AgentId("agent-b")].original_agent.architecture == ArchName("aarch64")
