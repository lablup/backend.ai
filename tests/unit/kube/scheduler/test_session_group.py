from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace

import pytest

from ai.backend.common.types import AgentSelectionStrategy
from ai.backend.kube.crd.session import (
    SessionGroupAdmission,
    SessionGroupDirection,
    SessionGroupEnforcement,
)
from ai.backend.kube.scheduler.cycle import (
    GroupPolicy,
    NodeState,
    PendingGroup,
    PendingPod,
    Placement,
    Resources,
    Skip,
    SkipReason,
    schedule,
)
from ai.backend.kube.scheduler.selection import NodeSelector

GIB = 1024**3
GROUP_ID = "33333333-0000-0000-0000-000000000001"
OTHER = "member-0"  # a session of the group placed in an earlier cycle


def _schedule(nodes: Sequence[NodeState], groups: Sequence[PendingGroup]) -> list[Placement | Skip]:
    # Concentrated piles sessions on the fullest node unless the group says otherwise.
    return schedule(nodes, groups, NodeSelector(AgentSelectionStrategy.CONCENTRATED))


def _node(name: str, cpu: int, used_cpu: int = 0, members: Sequence[str] = ()) -> NodeState:
    return NodeState(
        name=name,
        allocatable=Resources(cpu * 1000, 64 * GIB, 110),
        used=Resources(used_cpu * 1000, 0, 0),
        group_members={GROUP_ID: frozenset(members)} if members else {},
    )


def _policy(
    direction: SessionGroupDirection,
    enforcement: SessionGroupEnforcement = SessionGroupEnforcement.PREFERRED,
    *,
    all_or_none: bool = False,
    member_count: int | None = None,
) -> GroupPolicy:
    return GroupPolicy(
        id=GROUP_ID,
        direction=direction,
        enforcement=enforcement,
        admission=(
            SessionGroupAdmission.ALL_OR_NONE if all_or_none else SessionGroupAdmission.INDEPENDENT
        ),
        member_count=member_count,
    )


def _session(
    name: str,
    policy: GroupPolicy | None,
    *,
    cpu: int = 2,
    kernels: int = 1,
    priority: int = 0,
    created: str = "1",
    ready: int = 0,
    single_node: bool = False,
) -> PendingGroup:
    return PendingGroup(
        namespace="ns",
        name=name,
        priority=priority,
        created_at=created,
        min_member=kernels,
        pods=[
            PendingPod("ns", f"{name}-{i}", Resources(cpu * 1000, GIB, 1)) for i in range(kernels)
        ],
        required_levels=["kubernetes.io/hostname"] if single_node else (),
        session_id=name,
        session_group=policy,
        group_ready=ready,
    )


def _nodes_of(result: Placement | Skip) -> set[str]:
    assert isinstance(result, Placement)
    return set(result.nodes.values())


def _hostnames(nodes: Sequence[NodeState]) -> list[NodeState]:
    return [replace(n, labels={"kubernetes.io/hostname": n.name}) for n in nodes]


class TestSpread:
    @pytest.fixture
    def nodes(self) -> list[NodeState]:
        return [_node("a", 8, used_cpu=4, members=[OTHER]), _node("b", 8)]

    def test_preferred_puts_the_member_on_a_node_without_one(self, nodes: list[NodeState]) -> None:
        [result] = _schedule(nodes, [_session("s", _policy(SessionGroupDirection.SPREAD))])
        assert _nodes_of(result) == {"b"}

    def test_preferred_falls_back_to_a_node_with_a_member(self, nodes: list[NodeState]) -> None:
        nodes[1] = _node("b", 8, used_cpu=7)
        [result] = _schedule(nodes, [_session("s", _policy(SessionGroupDirection.SPREAD))])
        assert _nodes_of(result) == {"a"}

    def test_strict_does_not_fall_back(self, nodes: list[NodeState]) -> None:
        nodes[1] = _node("b", 8, members=["member-1"])
        policy = _policy(SessionGroupDirection.SPREAD, SessionGroupEnforcement.STRICT)
        [result] = _schedule(nodes, [_session("s", policy)])
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSCHEDULABLE

    def test_strict_counts_members_placed_in_the_same_cycle(self) -> None:
        nodes = [_node("a", 8), _node("b", 8), _node("c", 8)]
        policy = _policy(SessionGroupDirection.SPREAD, SessionGroupEnforcement.STRICT)
        results = _schedule(nodes, [_session(f"s{i}", policy, created=str(i)) for i in range(3)])
        assert set().union(*(_nodes_of(r) for r in results)) == {"a", "b", "c"}

    def test_a_session_does_not_count_against_itself(self) -> None:
        nodes = _hostnames([_node("a", 8), _node("b", 8, members=[OTHER])])
        policy = _policy(SessionGroupDirection.SPREAD, SessionGroupEnforcement.STRICT)
        [result] = _schedule(nodes, [_session("s", policy, kernels=2, single_node=True)])
        assert _nodes_of(result) == {"a"}


class TestPack:
    @pytest.fixture
    def nodes(self) -> list[NodeState]:
        return [_node("a", 8, members=[OTHER]), _node("b", 8, used_cpu=4)]

    def test_preferred_puts_the_member_with_the_others(self, nodes: list[NodeState]) -> None:
        [result] = _schedule(nodes, [_session("s", _policy(SessionGroupDirection.PACK))])
        assert _nodes_of(result) == {"a"}

    def test_preferred_falls_back_when_their_node_is_full(self, nodes: list[NodeState]) -> None:
        nodes[0] = _node("a", 8, used_cpu=7, members=[OTHER])
        [result] = _schedule(nodes, [_session("s", _policy(SessionGroupDirection.PACK))])
        assert _nodes_of(result) == {"b"}

    def test_strict_does_not_fall_back(self, nodes: list[NodeState]) -> None:
        nodes[0] = _node("a", 8, used_cpu=7, members=[OTHER])
        policy = _policy(SessionGroupDirection.PACK, SessionGroupEnforcement.STRICT)
        [result] = _schedule(nodes, [_session("s", policy)])
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSCHEDULABLE

    def test_strict_leaves_the_first_member_free(self) -> None:
        nodes = [_node("a", 8), _node("b", 8, used_cpu=4)]
        policy = _policy(SessionGroupDirection.PACK, SessionGroupEnforcement.STRICT)
        [result] = _schedule(nodes, [_session("s", policy)])
        assert _nodes_of(result) == {"b"}

    def test_strict_follows_the_anchor_placed_in_the_same_cycle(self) -> None:
        # Dispersed puts the anchor on "a", then would move the second to the emptier "b".
        nodes = [_node("a", 8), _node("b", 8, used_cpu=1)]
        policy = _policy(SessionGroupDirection.PACK, SessionGroupEnforcement.STRICT)
        sessions = [_session("s0", policy, created="0"), _session("s1", policy, created="1")]
        results = schedule(nodes, sessions, NodeSelector(AgentSelectionStrategy.DISPERSED))
        assert _nodes_of(results[0]) == _nodes_of(results[1])


class TestDirectionNone:
    def test_the_group_does_not_change_the_placement(self) -> None:
        nodes = [_node("a", 8, used_cpu=4, members=[OTHER]), _node("b", 8)]
        policy = _policy(SessionGroupDirection.NONE, SessionGroupEnforcement.STRICT)
        [result] = _schedule(nodes, [_session("s", policy)])
        assert _nodes_of(result) == {"a"}


class TestAllOrNone:
    @pytest.fixture
    def policy(self) -> GroupPolicy:
        return _policy(
            SessionGroupDirection.SPREAD,
            SessionGroupEnforcement.STRICT,
            all_or_none=True,
            member_count=3,
        )

    def _members(self, policy: GroupPolicy, ready: int, count: int = 3) -> list[PendingGroup]:
        return [_session(f"s{i}", policy, created=str(i), ready=ready) for i in range(count)]

    def test_waits_until_every_member_exists(self, policy: GroupPolicy) -> None:
        nodes = [_node("a", 8), _node("b", 8), _node("c", 8)]
        results = _schedule(nodes, self._members(policy, ready=2, count=2))
        assert [r.reason for r in results if isinstance(r, Skip)] == [
            SkipReason.WAITING_FOR_GROUP_MEMBERS
        ] * 2
        assert all(n.used.cpu_milli == 0 for n in nodes)

    def test_places_every_member_in_one_cycle(self, policy: GroupPolicy) -> None:
        nodes = [_node("a", 8), _node("b", 8), _node("c", 8)]
        results = _schedule(nodes, self._members(policy, ready=3))
        assert all(isinstance(r, Placement) for r in results)
        assert set().union(*(_nodes_of(r) for r in results)) == {"a", "b", "c"}

    def test_places_none_when_one_member_does_not_fit(self, policy: GroupPolicy) -> None:
        nodes = [_node("a", 8), _node("b", 8)]
        results = _schedule(nodes, self._members(policy, ready=3))
        assert [r.reason for r in results if isinstance(r, Skip)] == [
            SkipReason.GROUP_DOES_NOT_FIT
        ] * 3
        assert all(n.used.cpu_milli == 0 and not n.group_members for n in nodes)

    def test_goes_by_its_highest_member_priority(self, policy: GroupPolicy) -> None:
        nodes = [_node("a", 4), _node("b", 4), _node("c", 4)]
        members = self._members(policy, ready=3)
        members[2] = replace(members[2], priority=10, created_at="9")
        single = _session("other", None, cpu=4, priority=5, created="0")
        results = _schedule(nodes, [single, *members])
        by_name = {r.group.name: r for r in results}
        assert all(isinstance(by_name[m.name], Placement) for m in members)
        assert isinstance(by_name["other"], Skip)

    def test_a_blocked_group_keeps_its_nodes(self, policy: GroupPolicy) -> None:
        nodes = [_node("a", 8, used_cpu=7), _node("b", 8), _node("c", 8)]
        members = self._members(policy, ready=3)
        later = _session("later", None, created="9")
        results = _schedule(nodes, [*members, later])
        by_name = {r.group.name: r for r in results}
        later_result = by_name["later"]
        assert isinstance(later_result, Skip) and later_result.reason == SkipReason.RESERVED

    def test_needs_a_member_count(self) -> None:
        policy = _policy(SessionGroupDirection.SPREAD, all_or_none=True)
        [result] = _schedule([_node("a", 8)], [_session("s", policy, ready=1)])
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSUPPORTED


def _members_on(nodes: Sequence[NodeState]) -> Mapping[str, frozenset[str]]:
    return {n.name: n.group_members.get(GROUP_ID, frozenset()) for n in nodes}


class TestReservations:
    def test_a_placed_member_is_recorded_on_its_node(self) -> None:
        nodes = [_node("a", 8)]
        _schedule(nodes, [_session("s", _policy(SessionGroupDirection.SPREAD))])
        assert _members_on(nodes) == {"a": frozenset({"s"})}
