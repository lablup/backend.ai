from __future__ import annotations

from collections.abc import Mapping, Sequence

from ai.backend.kube.scheduler.cycle import (
    NodeState,
    PendingGroup,
    PendingPod,
    Placement,
    PlacementStrategy,
    QueueState,
    Resources,
    Skip,
    SkipReason,
    Taint,
    Toleration,
    schedule,
)

GIB = 1024**3


def _node(
    name: str,
    cpu: int,
    used_cpu: int = 0,
    *,
    labels: Mapping[str, str] | None = None,
    taints: Sequence[Taint] = (),
    schedulable: bool = True,
) -> NodeState:
    return NodeState(
        name=name,
        allocatable=Resources(cpu * 1000, 64 * GIB, 110),
        used=Resources(used_cpu * 1000, 0, 0),
        labels=labels or {},
        taints=taints,
        schedulable=schedulable,
    )


def _group(
    name: str,
    n: int,
    cpu: int,
    *,
    queue: str = "q",
    priority: int = 0,
    created: str = "1",
    tolerations: Sequence[Toleration] = (),
) -> PendingGroup:
    return PendingGroup(
        namespace="ns",
        name=name,
        queue=queue,
        priority=priority,
        created_at=created,
        min_member=n,
        pods=[
            PendingPod("ns", f"{name}-{i}", Resources(cpu * 1000, GIB, 1), tolerations=tolerations)
            for i in range(n)
        ],
    )


class TestGang:
    def test_places_every_pod_or_none(self) -> None:
        nodes = [_node("a", 8), _node("b", 8)]
        [result] = schedule(nodes, {}, [_group("g", 3, 6)])
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSCHEDULABLE
        assert all(n.used.cpu_milli == 0 for n in nodes)

    def test_spreads_a_gang_across_nodes_when_needed(self) -> None:
        nodes = [_node("a", 8), _node("b", 8)]
        [result] = schedule(nodes, {}, [_group("g", 2, 6)])
        assert isinstance(result, Placement)
        assert sorted(result.nodes.values()) == ["a", "b"]

    def test_waits_until_all_pods_exist(self) -> None:
        group = _group("g", 2, 1)
        partial = PendingGroup(**{**group.__dict__, "pods": group.pods[:1]})
        [result] = schedule([_node("a", 8)], {}, [partial])
        assert isinstance(result, Skip) and result.reason == SkipReason.WAITING_FOR_PODS


class TestQueue:
    def test_limit_holds_a_group_back(self) -> None:
        queues = {"q": QueueState("q", Resources(3000, 2**62, 2**62), Resources(2000, 0, 0))}
        [result] = schedule([_node("a", 8)], queues, [_group("g", 1, 2)])
        assert isinstance(result, Skip) and result.reason == SkipReason.QUEUE_LIMIT

    def test_usage_counts_groups_placed_in_the_same_cycle(self) -> None:
        queues = {"q": QueueState("q", Resources(3000, 2**62, 2**62))}
        results = schedule(
            [_node("a", 8)],
            queues,
            [_group("g1", 1, 2, created="1"), _group("g2", 1, 2, created="2")],
        )
        assert [type(r) for r in results] == [Placement, Skip]

    def test_skipped_group_does_not_block_later_ones(self) -> None:
        results = schedule(
            [_node("a", 8)],
            {},
            [_group("big", 1, 20, created="1"), _group("small", 1, 1, created="2")],
        )
        assert [type(r) for r in results] == [Skip, Placement]


class TestOrder:
    def test_priority_before_age(self) -> None:
        results = schedule(
            [_node("a", 4)],
            {},
            [_group("old", 1, 4, created="1"), _group("urgent", 1, 4, priority=10, created="2")],
        )
        placed = [r.group.name for r in results if isinstance(r, Placement)]
        assert placed == ["urgent"]


class TestNodeFilter:
    def test_untolerated_taint_excludes_node(self) -> None:
        nodes = [_node("tainted", 8, taints=[Taint("gpu", None, "NoSchedule")]), _node("plain", 8)]
        [result] = schedule(nodes, {}, [_group("g", 1, 1)])
        assert isinstance(result, Placement) and result.nodes == {"g-0": "plain"}

    def test_toleration_admits_node(self) -> None:
        nodes = [_node("tainted", 8, taints=[Taint("gpu", None, "NoSchedule")])]
        group = _group("g", 1, 1, tolerations=[Toleration("gpu", "Exists", None, None)])
        [result] = schedule(nodes, {}, [group])
        assert isinstance(result, Placement)

    def test_unschedulable_node_is_skipped(self) -> None:
        [result] = schedule([_node("a", 8, schedulable=False)], {}, [_group("g", 1, 1)])
        assert isinstance(result, Skip)


class TestStrategy:
    def test_concentrated_fills_the_busiest_node(self) -> None:
        nodes = [_node("idle", 8), _node("busy", 8, used_cpu=4)]
        [result] = schedule(nodes, {}, [_group("g", 1, 1)], PlacementStrategy.CONCENTRATED)
        assert isinstance(result, Placement) and result.nodes == {"g-0": "busy"}

    def test_dispersed_uses_the_idlest_node(self) -> None:
        nodes = [_node("idle", 8), _node("busy", 8, used_cpu=4)]
        [result] = schedule(nodes, {}, [_group("g", 1, 1)], PlacementStrategy.DISPERSED)
        assert isinstance(result, Placement) and result.nodes == {"g-0": "idle"}


class TestQueueHierarchy:
    def test_parent_limit_holds_a_child_back(self) -> None:
        queues = {
            "rg": QueueState("rg", Resources(4000, 2**62, 2**62), Resources(3000, 0, 0)),
            "rg.p1": QueueState("rg.p1", None, parent="rg"),
        }
        [result] = schedule([_node("a", 8)], queues, [_group("g", 1, 2, queue="rg.p1")])
        assert isinstance(result, Skip) and result.reason == SkipReason.QUEUE_LIMIT
        assert "rg " in result.message + " "

    def test_placement_counts_against_every_ancestor(self) -> None:
        queues = {
            "rg": QueueState("rg", Resources(4000, 2**62, 2**62)),
            "rg.p1": QueueState("rg.p1", None, parent="rg"),
            "rg.p2": QueueState("rg.p2", None, parent="rg"),
        }
        results = schedule(
            [_node("a", 8)],
            queues,
            [
                _group("g1", 1, 3, queue="rg.p1", created="1"),
                _group("g2", 1, 3, queue="rg.p2", created="2"),
            ],
        )
        assert [type(r) for r in results] == [Placement, Skip]

    def test_higher_fair_share_factor_goes_first(self) -> None:
        queues = {
            "heavy": QueueState("heavy", None, fair_share_factor=0.2),
            "light": QueueState("light", None, fair_share_factor=0.9),
        }
        results = schedule(
            [_node("a", 4)],
            queues,
            [
                _group("old", 1, 4, queue="heavy", created="1"),
                _group("new", 1, 4, queue="light", created="2"),
            ],
        )
        placed = [r.group.name for r in results if isinstance(r, Placement)]
        assert placed == ["new"]


class TestDevices:
    def test_pod_goes_to_a_node_with_free_devices(self) -> None:
        nodes = [
            NodeState("cpu-only", Resources(8000, 64 * GIB, 110), Resources()),
            NodeState("gpu", Resources(8000, 64 * GIB, 110), Resources(), devices={"cuda.dra": 4}),
        ]
        group = PendingGroup(
            "ns",
            "g",
            "q",
            0,
            "1",
            1,
            [PendingPod("ns", "g-0", Resources(1000, GIB, 1), devices={"cuda.dra": 2})],
        )
        [result] = schedule(nodes, {}, [group])
        assert isinstance(result, Placement) and result.nodes == {"g-0": "gpu"}

    def test_used_devices_hold_a_gang_back(self) -> None:
        nodes = [
            NodeState(
                "gpu",
                Resources(8000, 64 * GIB, 110),
                Resources(),
                devices={"cuda.dra": 4},
                devices_used={"cuda.dra": 3},
            )
        ]
        group = PendingGroup(
            "ns",
            "g",
            "q",
            0,
            "1",
            2,
            [
                PendingPod("ns", f"g-{i}", Resources(1000, GIB, 1), devices={"cuda.dra": 1})
                for i in range(2)
            ],
        )
        [result] = schedule(nodes, {}, [group])
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSCHEDULABLE


class TestRequiredLevels:
    def _nodes(self) -> list[NodeState]:
        return [
            NodeState(
                name,
                Resources(4000, 64 * GIB, 110),
                Resources(),
                labels={"kubernetes.io/hostname": name},
            )
            for name in ("a", "b")
        ]

    def _group(self, levels: Sequence[str]) -> PendingGroup:
        return PendingGroup(
            "ns",
            "g",
            "q",
            0,
            "1",
            2,
            [PendingPod("ns", f"g-{i}", Resources(3000, GIB, 1)) for i in range(2)],
            required_levels=levels,
        )

    def test_without_levels_pods_spread_when_they_must(self) -> None:
        [result] = schedule(self._nodes(), {}, [self._group([])])
        assert isinstance(result, Placement) and set(result.nodes.values()) == {"a", "b"}

    def test_hostname_level_keeps_the_group_on_one_node(self) -> None:
        [result] = schedule(self._nodes(), {}, [self._group(["kubernetes.io/hostname"])])
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSCHEDULABLE

    def test_a_domain_that_fits_is_found(self) -> None:
        nodes = self._nodes()
        nodes.append(
            NodeState(
                "big",
                Resources(8000, 64 * GIB, 110),
                Resources(),
                labels={"kubernetes.io/hostname": "big"},
            )
        )
        [result] = schedule(nodes, {}, [self._group(["kubernetes.io/hostname"])])
        assert isinstance(result, Placement) and set(result.nodes.values()) == {"big"}


class TestSharedDevices:
    def test_a_shared_device_needs_a_node_with_the_driver(self) -> None:
        nodes = [
            NodeState("busy-cpu-only", Resources(8000, 64 * GIB, 110), Resources(4000, 0, 1)),
            NodeState(
                "gpu",
                Resources(8000, 64 * GIB, 110),
                Resources(),
                devices={"cuda.dra": 1},
                devices_used={"cuda.dra": 1},
            ),
        ]
        group = PendingGroup(
            "ns",
            "g",
            "q",
            0,
            "1",
            1,
            [PendingPod("ns", "g-0", Resources(1000, GIB, 1), shared_devices={"cuda.dra": 1})],
        )
        [result] = schedule(nodes, {}, [group])
        assert isinstance(result, Placement) and result.nodes == {"g-0": "gpu"}
