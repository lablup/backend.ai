from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace

from ai.backend.common.types import AgentSelectionStrategy
from ai.backend.kube.crd.device import GPUAllocationPolicy
from ai.backend.kube.scheduler.cycle import (
    NodeState,
    PendingGroup,
    PendingPod,
    Placement,
    Resources,
    ShareOption,
    ShareRequest,
    Skip,
    SkipReason,
    Taint,
    Toleration,
    schedule,
)
from ai.backend.kube.scheduler.selection import NodeSelector

GIB = 1024**3


def _schedule(
    nodes: Sequence[NodeState],
    groups: Sequence[PendingGroup],
    strategy: AgentSelectionStrategy = AgentSelectionStrategy.CONCENTRATED,
    policy: GPUAllocationPolicy = GPUAllocationPolicy.BAI,
) -> list[Placement | Skip]:
    return schedule(nodes, groups, NodeSelector(strategy), policy)


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
    priority: int = 0,
    created: str = "1",
    tolerations: Sequence[Toleration] = (),
) -> PendingGroup:
    return PendingGroup(
        namespace="ns",
        name=name,
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
        [result] = _schedule(nodes, [_group("g", 3, 6)])
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSCHEDULABLE
        assert all(n.used.cpu_milli == 0 for n in nodes)

    def test_spreads_a_gang_across_nodes_when_needed(self) -> None:
        nodes = [_node("a", 8), _node("b", 8)]
        [result] = _schedule(nodes, [_group("g", 2, 6)])
        assert isinstance(result, Placement)
        assert sorted(result.nodes.values()) == ["a", "b"]

    def test_waits_until_all_pods_exist(self) -> None:
        group = _group("g", 2, 1)
        partial = PendingGroup(**{**group.__dict__, "pods": group.pods[:1]})
        [result] = _schedule([_node("a", 8)], [partial])
        assert isinstance(result, Skip) and result.reason == SkipReason.WAITING_FOR_PODS

    def test_only_the_missing_members_of_a_partly_placed_gang_are_placed(self) -> None:
        group = _group("g", 3, 1)
        partial = replace(group, pods=group.pods[:1], placed_members=2, placed_nodes=["a"])
        [result] = _schedule([_node("a", 8)], [partial])
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
        [result] = _schedule(nodes, [partial])
        assert isinstance(result, Skip) and result.reason == SkipReason.UNSCHEDULABLE


class TestOrder:
    def test_priority_before_age(self) -> None:
        results = _schedule(
            [_node("a", 4)],
            [_group("old", 1, 4, created="1"), _group("urgent", 1, 4, priority=10, created="2")],
        )
        placed = [r.group.name for r in results if isinstance(r, Placement)]
        assert placed == ["urgent"]


class TestNodeFilter:
    def test_untolerated_taint_excludes_node(self) -> None:
        nodes = [_node("tainted", 8, taints=[Taint("gpu", None, "NoSchedule")]), _node("plain", 8)]
        [result] = _schedule(nodes, [_group("g", 1, 1)])
        assert isinstance(result, Placement) and result.nodes == {"g-0": "plain"}

    def test_toleration_admits_node(self) -> None:
        nodes = [_node("tainted", 8, taints=[Taint("gpu", None, "NoSchedule")])]
        group = _group("g", 1, 1, tolerations=[Toleration("gpu", "Exists", None, None)])
        [result] = _schedule(nodes, [group])
        assert isinstance(result, Placement)

    def test_unschedulable_node_is_skipped(self) -> None:
        [result] = _schedule([_node("a", 8, schedulable=False)], [_group("g", 1, 1)])
        assert isinstance(result, Skip)


class TestStrategy:
    def test_concentrated_fills_the_busiest_node(self) -> None:
        nodes = [_node("idle", 8), _node("busy", 8, used_cpu=4)]
        [result] = _schedule(nodes, [_group("g", 1, 1)], AgentSelectionStrategy.CONCENTRATED)
        assert isinstance(result, Placement) and result.nodes == {"g-0": "busy"}

    def test_dispersed_uses_the_idlest_node(self) -> None:
        nodes = [_node("idle", 8), _node("busy", 8, used_cpu=4)]
        [result] = _schedule(nodes, [_group("g", 1, 1)], AgentSelectionStrategy.DISPERSED)
        assert isinstance(result, Placement) and result.nodes == {"g-0": "idle"}


class TestDevices:
    def test_pod_goes_to_a_node_with_free_devices(self) -> None:
        nodes = [
            NodeState("cpu-only", Resources(8000, 64 * GIB, 110), Resources()),
            NodeState("gpu", Resources(8000, 64 * GIB, 110), Resources(), devices={"cuda.dra": 4}),
        ]
        group = PendingGroup(
            "ns",
            "g",
            0,
            "1",
            1,
            [PendingPod("ns", "g-0", Resources(1000, GIB, 1), devices={"cuda.dra": 2})],
        )
        [result] = _schedule(nodes, [group])
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
            0,
            "1",
            2,
            [
                PendingPod("ns", f"g-{i}", Resources(1000, GIB, 1), devices={"cuda.dra": 1})
                for i in range(2)
            ],
        )
        [result] = _schedule(nodes, [group])
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
            0,
            "1",
            2,
            [PendingPod("ns", f"g-{i}", Resources(3000, GIB, 1)) for i in range(2)],
            required_levels=levels,
        )

    def test_without_levels_pods_spread_when_they_must(self) -> None:
        [result] = _schedule(self._nodes(), [self._group([])])
        assert isinstance(result, Placement) and set(result.nodes.values()) == {"a", "b"}

    def test_hostname_level_keeps_the_group_on_one_node(self) -> None:
        [result] = _schedule(self._nodes(), [self._group(["kubernetes.io/hostname"])])
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
        [result] = _schedule(nodes, [self._group(["kubernetes.io/hostname"])])
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
            0,
            "1",
            1,
            [PendingPod("ns", "g-0", Resources(1000, GIB, 1), shared_devices={"cuda.dra": 1})],
        )
        [result] = _schedule(nodes, [group])
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
    return PendingGroup("ns", "g", 0, "1", 1, [pod])


class TestShares:
    def test_a_split_request_needs_distinct_devices(self) -> None:
        part = ShareRequest("gpu.x", (ShareOption(900),))
        [result] = _schedule([_share_node("n", {"d1": 500})], [_share_group((part, part))])
        assert isinstance(result, Skip)
        [result] = _schedule([_share_node("n")], [_share_group((part, part))])
        assert isinstance(result, Placement)

    def test_first_available_takes_the_first_option_that_fits(self) -> None:
        pick = ShareRequest("gpu.x", (ShareOption(2000), ShareOption(1600)))
        node = _share_node("n")
        [result] = _schedule([node], [_share_group((pick,))])
        assert isinstance(result, Placement)
        assert node.share_used == {"gpu.x": {"d0": 1600}}

    def test_a_request_without_shares_takes_a_whole_unused_device(self) -> None:
        whole = ShareRequest("gpu.x", (ShareOption(None),))
        node = _share_node("n", {"d0": 1, "d1": 1})
        [result] = _schedule([node], [_share_group((whole,))])
        assert isinstance(result, Skip)

    def test_whole_devices_take_their_full_capacity(self) -> None:
        whole = ShareRequest("gpu.x", (ShareOption(None, 2),))
        node = _share_node("n")
        [result] = _schedule([node], [_share_group((whole,))])
        assert isinstance(result, Placement)
        assert node.share_used == {"gpu.x": {"d0": 1650, "d1": 1000}}
        part = ShareRequest("gpu.x", (ShareOption(1),))
        [result] = _schedule([node], [_share_group((part,))])
        assert isinstance(result, Skip)

    def test_the_device_plugin_policy_refuses_shares(self) -> None:
        part = ShareRequest("gpu.x", (ShareOption(100),))
        [result] = _schedule(
            [_share_node("n")],
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
        [result] = _schedule(nodes, [PendingGroup("ns", "g", 0, "1", 1, [pod])])
        assert isinstance(result, Placement) and result.nodes == {"g-0": "free"}


class TestHead:
    def test_skipped_group_does_not_block_later_ones(self) -> None:
        results = _schedule(
            [_node("a", 8)], [_group("big", 1, 20, created="1"), _group("small", 1, 1, created="2")]
        )
        assert [type(r) for r in results] == [Skip, Placement]

    def test_a_blocked_first_group_keeps_its_nodes_from_later_groups(self) -> None:
        nodes = [_node("a", 8, used_cpu=4)]
        results = _schedule(
            nodes, [_group("big", 1, 6, created="1"), _group("small", 1, 1, created="2")]
        )
        assert [r.reason for r in results if isinstance(r, Skip)] == [
            SkipReason.UNSCHEDULABLE,
            SkipReason.RESERVED,
        ]

    def test_later_groups_use_the_nodes_the_first_cannot(self) -> None:
        nodes = [
            _node("a", 8, used_cpu=4),
            _node("other", 8, taints=[Taint("gpu", None, "NoSchedule")]),
        ]
        small = _group(
            "small", 1, 1, created="2", tolerations=[Toleration("gpu", "Exists", None, None)]
        )
        results = _schedule(nodes, [_group("big", 1, 6, created="1"), small])
        assert isinstance(results[1], Placement) and results[1].nodes == {"small-0": "other"}


class TestOrderByCreation:
    def test_the_older_session_goes_first_at_the_same_priority(self) -> None:
        results = _schedule(
            [_node("a", 4)],
            [_group("new", 1, 4, created="2026-01-02"), _group("old", 1, 4, created="2026-01-01")],
        )
        assert [r.group.name for r in results if isinstance(r, Placement)] == ["old"]


class TestSokovanCoreSelection:
    def test_roundrobin_turns_over_the_nodes(self) -> None:
        nodes = [_node("a", 8), _node("b", 8)]
        selector = NodeSelector(AgentSelectionStrategy.ROUNDROBIN)
        placed = []
        for i in range(4):
            [result] = schedule(nodes, [_group(f"g{i}", 1, 1)], selector)
            assert isinstance(result, Placement)
            placed.append(result.nodes[f"g{i}-0"])
        assert placed == ["a", "b", "a", "b"]

    def test_concentrated_keeps_device_nodes_free_for_device_pods(self) -> None:
        nodes = [
            NodeState(
                "gpu",
                Resources(8000, 64 * GIB, 110),
                Resources(6000, 0, 1),
                devices={"cuda.dra": 4, "cuda.dra/cuda.device": 4},
            ),
            NodeState("cpu", Resources(8000, 64 * GIB, 110), Resources()),
        ]
        [result] = _schedule(nodes, [_group("g", 1, 1)])
        assert isinstance(result, Placement) and result.nodes == {"g-0": "cpu"}

    def test_a_pod_asking_an_architecture_goes_to_a_node_of_it(self) -> None:
        nodes = [
            _node("arm", 8, labels={"kubernetes.io/arch": "arm64"}),
            _node("x86", 8, used_cpu=4, labels={"kubernetes.io/arch": "amd64"}),
        ]
        group = _group("g", 1, 1)
        pod = replace(group.pods[0], node_selector={"kubernetes.io/arch": "arm64"})
        [result] = _schedule(nodes, [replace(group, pods=[pod])])
        assert isinstance(result, Placement) and result.nodes == {"g-0": "arm"}
