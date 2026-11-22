from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from decimal import Decimal

from ai.backend.kube.crd.device import GPUAllocationPolicy
from ai.backend.kube.scheduler.cycle import (
    NodeState,
    PendingGroup,
    PendingPod,
    Placement,
    PlacementStrategy,
    QueueState,
    Resources,
    ShareOption,
    ShareRequest,
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

    def test_only_the_missing_members_of_a_partly_placed_gang_are_placed(self) -> None:
        group = _group("g", 3, 1)
        partial = replace(group, pods=group.pods[:1], placed_members=2, placed_nodes=["a"])
        [result] = schedule([_node("a", 8)], {}, [partial])
        assert isinstance(result, Placement) and result.nodes == {"g-0": "a"}

    def test_missing_members_join_the_domain_of_the_placed_ones(self) -> None:
        nodes = [
            _node("a", 8, labels={"rack": "r1"}),
            _node("b", 8, labels={"rack": "r2"}, used_cpu=7),
        ]
        group = _group("g", 2, 2)
        partial = replace(
            group,
            pods=group.pods[:1],
            placed_members=1,
            placed_nodes=["b"],
            required_levels=["rack"],
        )
        [result] = schedule(nodes, {}, [partial])
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSCHEDULABLE


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

    def test_a_blocked_head_keeps_its_nodes_from_later_groups_of_its_queue(self) -> None:
        nodes = [_node("a", 8, used_cpu=4)]
        results = schedule(
            nodes, {}, [_group("big", 1, 6, created="1"), _group("small", 1, 1, created="2")]
        )
        assert [r.reason for r in results if isinstance(r, Skip)] == [
            SkipReason.UNSCHEDULABLE,
            SkipReason.RESERVED,
        ]

    def test_a_blocked_head_does_not_hold_other_queues(self) -> None:
        nodes = [_node("a", 8, used_cpu=4)]
        results = schedule(
            nodes,
            {},
            [_group("big", 1, 6, created="1"), _group("other", 1, 1, queue="q2", created="2")],
        )
        assert [type(r) for r in results] == [Skip, Placement]

    def test_device_slot_limit_holds_a_group_back(self) -> None:
        queues = {
            "q": QueueState(
                "q",
                None,
                slot_limits={"cuda.device": Decimal(2)},
                slot_used={"cuda.device": Decimal(1)},
            )
        }
        group = _group("g", 1, 1)
        heavy = replace(group, pods=[replace(group.pods[0], slots={"cuda.device": Decimal(2)})])
        [result] = schedule([_node("a", 8)], queues, [heavy])
        assert isinstance(result, Skip) and result.reason == SkipReason.QUEUE_LIMIT


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


def _share_node(name: str, used: Mapping[str, int] | None = None) -> NodeState:
    return NodeState(
        name,
        Resources(8000, 64 * GIB, 110),
        Resources(),
        share_capacity={"gpu.x": {"d0": 1650, "d1": 1000}},
        share_used={"gpu.x": dict(used or {})},
    )


def _share_group(*claims: tuple[ShareRequest, ...]) -> PendingGroup:
    pod = PendingPod("ns", "g-0", Resources(1000, GIB, 1), share_claims=list(claims))
    return PendingGroup("ns", "g", "q", 0, "1", 1, [pod])


class TestShares:
    def test_a_split_request_needs_distinct_devices(self) -> None:
        part = ShareRequest("gpu.x", (ShareOption(900),))
        [result] = schedule([_share_node("n", {"d1": 500})], {}, [_share_group((part, part))])
        assert isinstance(result, Skip)
        [result] = schedule([_share_node("n")], {}, [_share_group((part, part))])
        assert isinstance(result, Placement)

    def test_first_available_takes_the_first_option_that_fits(self) -> None:
        pick = ShareRequest("gpu.x", (ShareOption(2000), ShareOption(1600)))
        node = _share_node("n")
        [result] = schedule([node], {}, [_share_group((pick,))])
        assert isinstance(result, Placement)
        assert node.share_used == {"gpu.x": {"d0": 1600}}

    def test_a_request_without_shares_takes_a_whole_unused_device(self) -> None:
        whole = ShareRequest("gpu.x", (ShareOption(None),))
        node = _share_node("n", {"d0": 1, "d1": 1})
        [result] = schedule([node], {}, [_share_group((whole,))])
        assert isinstance(result, Skip)

    def test_the_device_plugin_policy_refuses_shares(self) -> None:
        part = ShareRequest("gpu.x", (ShareOption(100),))
        [result] = schedule(
            [_share_node("n")],
            {},
            [_share_group((part,))],
            policy=GPUAllocationPolicy.DEVICE_PLUGIN,
        )
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSUPPORTED


class TestExtendedResources:
    def test_a_pod_goes_where_the_extended_resource_is_free(self) -> None:
        nodes = [
            NodeState(
                "full",
                Resources(8000, 64 * GIB, 110),
                Resources(),
                extended={"nvidia.com/gpu": 4},
                extended_used={"nvidia.com/gpu": 4},
            ),
            NodeState(
                "free", Resources(8000, 64 * GIB, 110), Resources(), extended={"nvidia.com/gpu": 4}
            ),
        ]
        pod = PendingPod("ns", "g-0", Resources(1000, GIB, 1), extended={"nvidia.com/gpu": 2})
        [result] = schedule(nodes, {}, [PendingGroup("ns", "g", "q", 0, "1", 1, [pod])])
        assert isinstance(result, Placement) and result.nodes == {"g-0": "free"}
