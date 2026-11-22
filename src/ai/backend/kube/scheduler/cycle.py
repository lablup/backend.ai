"""One scheduling cycle over a snapshot: queue limits, ordering, gang placement. No API calls."""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace


class PlacementStrategy(enum.StrEnum):
    CONCENTRATED = "concentrated"  # fill the busiest node that fits first (binpack)
    DISPERSED = "dispersed"  # use the least busy node first (spread)


class SkipReason(enum.StrEnum):
    WAITING_FOR_PODS = "WaitingForPods"
    QUEUE_LIMIT = "QueueLimit"
    UNSCHEDULABLE = "Unschedulable"


@dataclass(frozen=True)
class Resources:
    cpu_milli: int = 0
    memory: int = 0
    pods: int = 0

    def __add__(self, other: Resources) -> Resources:
        return Resources(
            self.cpu_milli + other.cpu_milli, self.memory + other.memory, self.pods + other.pods
        )

    def __sub__(self, other: Resources) -> Resources:
        return Resources(
            self.cpu_milli - other.cpu_milli, self.memory - other.memory, self.pods - other.pods
        )

    def fits_in(self, capacity: Resources) -> bool:
        return (
            self.cpu_milli <= capacity.cpu_milli
            and self.memory <= capacity.memory
            and self.pods <= capacity.pods
        )


@dataclass(frozen=True)
class Taint:
    key: str
    value: str | None
    effect: str


@dataclass(frozen=True)
class Toleration:
    key: str | None
    operator: str  # "Equal" | "Exists"
    value: str | None
    effect: str | None

    def tolerates(self, taint: Taint) -> bool:
        if self.effect is not None and self.effect != taint.effect:
            return False
        if self.key is None:
            return self.operator == "Exists"
        if self.key != taint.key:
            return False
        return self.operator == "Exists" or self.value == taint.value


@dataclass
class NodeState:
    name: str
    allocatable: Resources
    used: Resources
    labels: Mapping[str, str] = field(default_factory=dict)
    taints: Sequence[Taint] = ()
    schedulable: bool = True
    # Devices on the node by "<DRA driver>" and by "<DRA driver>/<slot>"
    devices: Mapping[str, int] = field(default_factory=dict)
    devices_used: Mapping[str, int] = field(default_factory=dict)

    @property
    def free(self) -> Resources:
        return self.allocatable - self.used

    def has_devices(self, demand: Mapping[str, int], shared: Mapping[str, int]) -> bool:
        """Free whole devices for `demand`; for `shared`, only that the devices exist (the DRA
        allocator decides whether the shares fit)."""
        return all(
            self.devices.get(driver, 0) - self.devices_used.get(driver, 0) >= count
            for driver, count in demand.items()
        ) and all(self.devices.get(driver, 0) >= count for driver, count in shared.items())

    def take_devices(self, demand: Mapping[str, int]) -> None:
        used = dict(self.devices_used)
        for driver, count in demand.items():
            used[driver] = used.get(driver, 0) + count
        self.devices_used = used


@dataclass(frozen=True)
class PendingPod:
    namespace: str
    name: str
    requests: Resources
    node_selector: Mapping[str, str] = field(default_factory=dict)
    tolerations: Sequence[Toleration] = ()
    devices: Mapping[str, int] = field(default_factory=dict)  # "<DRA driver>/<slot>" → wanted
    shared_devices: Mapping[str, int] = field(default_factory=dict)  # DRA driver → devices shared


@dataclass(frozen=True)
class PendingGroup:
    namespace: str
    name: str
    queue: str
    priority: int
    created_at: str
    min_member: int
    pods: Sequence[PendingPod]
    required_levels: Sequence[str] = ()  # node labels every pod of the group shares a value of


@dataclass
class QueueState:
    name: str
    limit: Resources | None  # None: no limit
    used: Resources = field(default_factory=Resources)
    parent: str | None = None
    fair_share_factor: float = 0.0  # higher goes first, as in the Manager's fair share


def queue_chain(queues: Mapping[str, QueueState], name: str) -> list[QueueState]:
    """The queue and its ancestors; a cycle or a missing parent ends the chain."""
    chain: list[QueueState] = []
    current = queues.get(name)
    while current is not None and current not in chain:
        chain.append(current)
        current = queues.get(current.parent) if current.parent else None
    return chain


@dataclass(frozen=True)
class Placement:
    group: PendingGroup
    nodes: Mapping[str, str]  # pod name → node name


@dataclass(frozen=True)
class Skip:
    group: PendingGroup
    reason: SkipReason
    message: str


def _eligible(node: NodeState, pod: PendingPod) -> bool:
    if not node.schedulable:
        return False
    if any(node.labels.get(k) != v for k, v in pod.node_selector.items()):
        return False
    blocking = [t for t in node.taints if t.effect in ("NoSchedule", "NoExecute")]
    return all(any(tol.tolerates(t) for tol in pod.tolerations) for t in blocking)


def _choose(
    nodes: Sequence[NodeState], pod: PendingPod, strategy: PlacementStrategy
) -> NodeState | None:
    candidates = [
        n
        for n in nodes
        if _eligible(n, pod)
        and pod.requests.fits_in(n.free)
        and n.has_devices(pod.devices, pod.shared_devices)
    ]
    if not candidates:
        return None

    def busy(n: NodeState) -> tuple[float, str]:
        share = n.used.cpu_milli / n.allocatable.cpu_milli if n.allocatable.cpu_milli else 1.0
        return share, n.name

    if strategy == PlacementStrategy.CONCENTRATED:
        return max(candidates, key=busy)
    return min(candidates, key=busy)


def _domains(nodes: Sequence[NodeState], levels: Sequence[str]) -> list[list[NodeState]]:
    """Nodes grouped by their values of the required levels; a node lacking one is left out."""
    if not levels:
        return [list(nodes)]
    domains: dict[tuple[str, ...], list[NodeState]] = {}
    for node in nodes:
        if all(level in node.labels for level in levels):
            key = tuple(node.labels[level] for level in levels)
            domains.setdefault(key, []).append(node)
    return [domains[k] for k in sorted(domains)]


def _place_gang(
    nodes: Sequence[NodeState], group: PendingGroup, strategy: PlacementStrategy
) -> dict[str, str] | None:
    """The first topology domain that takes every pod of the group."""
    for domain in _domains(nodes, group.required_levels):
        placed = _place_in(domain, group, strategy)
        if placed is not None:
            return placed
    return None


def _place_in(
    nodes: Sequence[NodeState], group: PendingGroup, strategy: PlacementStrategy
) -> dict[str, str] | None:
    """Place every pod of the group on a tentative copy; nothing changes unless all fit."""
    trial = [replace(n) for n in nodes]
    placed: dict[str, str] = {}

    def size(p: PendingPod) -> tuple[int, int, int]:
        return (-sum(p.devices.values()), -p.requests.cpu_milli, -p.requests.memory)

    for pod in sorted(group.pods, key=size):
        node = _choose(trial, pod, strategy)
        if node is None:
            return None
        node.used = node.used + pod.requests
        node.take_devices(pod.devices)
        placed[pod.name] = node.name
    for original, tried in zip(nodes, trial, strict=True):
        original.used = tried.used
        original.devices_used = tried.devices_used
    return placed


def schedule(
    nodes: Sequence[NodeState],
    queues: Mapping[str, QueueState],
    groups: Sequence[PendingGroup],
    strategy: PlacementStrategy = PlacementStrategy.CONCENTRATED,
) -> list[Placement | Skip]:
    """Decide which pending groups start now: higher priority, then the queue with the higher
    fair share factor, then the oldest."""

    def order(g: PendingGroup) -> tuple[int, float, str, str]:
        queue = queues.get(g.queue)
        return (-g.priority, -(queue.fair_share_factor if queue else 0.0), g.created_at, g.name)

    results: list[Placement | Skip] = []
    for group in sorted(groups, key=order):
        if len(group.pods) < group.min_member:
            results.append(
                Skip(
                    group,
                    SkipReason.WAITING_FOR_PODS,
                    f"{len(group.pods)} of {group.min_member} pods exist",
                )
            )
            continue
        demand = Resources()
        for pod in group.pods:
            demand = demand + pod.requests
        chain = queue_chain(queues, group.queue)
        full = next(
            (q for q in chain if q.limit is not None and not (q.used + demand).fits_in(q.limit)),
            None,
        )
        if full is not None:
            results.append(
                Skip(group, SkipReason.QUEUE_LIMIT, f"queue {full.name} is at its limit")
            )
            continue
        placed = _place_gang(nodes, group, strategy)
        if placed is None:
            results.append(
                Skip(group, SkipReason.UNSCHEDULABLE, "not every pod of the group fits now")
            )
            continue
        for q in chain:
            q.used = q.used + demand
        results.append(Placement(group, placed))
    return results
