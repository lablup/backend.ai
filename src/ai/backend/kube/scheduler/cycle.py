"""One scheduling cycle over a snapshot: queue limits, ordering, gang placement. No API calls."""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from decimal import Decimal


class PlacementStrategy(enum.StrEnum):
    CONCENTRATED = "concentrated"  # fill the busiest node that fits first (binpack)
    DISPERSED = "dispersed"  # use the least busy node first (spread)


class GpuAllocationPolicy(enum.StrEnum):
    """Who holds the NVIDIA GPUs of the cluster (suggestion 4.11)."""

    DRA = "dra"  # devices only through ResourceClaims
    DEVICE_PLUGIN = "device-plugin"  # whole GPUs as an extended resource; no shares


class SkipReason(enum.StrEnum):
    WAITING_FOR_PODS = "WaitingForPods"
    QUEUE_LIMIT = "QueueLimit"
    UNSCHEDULABLE = "Unschedulable"
    RESERVED = "WaitingForQueueHead"
    UNSUPPORTED = "Unsupported"


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
class ShareOption:
    """`count` distinct devices with `shares` (0.01-share units) free on each; `None` takes
    a whole unused device."""

    shares: int | None
    count: int = 1


@dataclass(frozen=True)
class ShareRequest:
    """One request of a claim on a device with `shares` capacity; the first option that fits
    is taken (`firstAvailable`)."""

    driver: str
    options: tuple[ShareOption, ...]


type ShareClaim = tuple[ShareRequest, ...]  # its requests land on distinct devices
type ShareTake = dict[tuple[str, str], int]  # (driver, device) → shares


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
    # Extended resources (device plugins) by resource name
    extended: Mapping[str, int] = field(default_factory=dict)
    extended_used: Mapping[str, int] = field(default_factory=dict)
    # Devices with `shares` capacity: driver → device → shares
    share_capacity: Mapping[str, Mapping[str, int]] = field(default_factory=dict)
    share_used: Mapping[str, Mapping[str, int]] = field(default_factory=dict)

    @property
    def free(self) -> Resources:
        return self.allocatable - self.used

    def has_devices(self, demand: Mapping[str, int], shared: Mapping[str, int]) -> bool:
        """Free whole devices for `demand`; for `shared`, only that the devices exist."""
        return all(
            self.devices.get(driver, 0) - self.devices_used.get(driver, 0) >= count
            for driver, count in demand.items()
        ) and all(self.devices.get(driver, 0) >= count for driver, count in shared.items())

    def take_devices(self, demand: Mapping[str, int]) -> None:
        used = dict(self.devices_used)
        for driver, count in demand.items():
            used[driver] = used.get(driver, 0) + count
        self.devices_used = used

    def has_extended(self, demand: Mapping[str, int]) -> bool:
        return all(
            self.extended.get(name, 0) - self.extended_used.get(name, 0) >= count
            for name, count in demand.items()
        )

    def take_extended(self, demand: Mapping[str, int]) -> None:
        used = dict(self.extended_used)
        for name, count in demand.items():
            used[name] = used.get(name, 0) + count
        self.extended_used = used

    def fit_shares(self, claims: Sequence[ShareClaim]) -> ShareTake | None:
        """Shares taken per device for `claims`, best fit first; None if they do not fit."""
        take: ShareTake = {}
        for claim in claims:
            in_claim: set[tuple[str, str]] = set()
            for request in claim:
                picked = next(
                    (
                        p
                        for option in request.options
                        if (p := self._pick(request.driver, option, take, in_claim)) is not None
                    ),
                    None,
                )
                if picked is None:
                    return None
                for key, shares in picked:
                    take[key] = take.get(key, 0) + shares
                    in_claim.add(key)
        return take

    def _pick(
        self,
        driver: str,
        option: ShareOption,
        take: ShareTake,
        exclude: set[tuple[str, str]],
    ) -> list[tuple[tuple[str, str], int]] | None:
        capacity = self.share_capacity.get(driver) or {}
        used = self.share_used.get(driver) or {}
        candidates = []
        for device, cap in capacity.items():
            key = (driver, device)
            if key in exclude:
                continue
            taken = used.get(device, 0) + take.get(key, 0)
            need = cap if option.shares is None else option.shares
            if (option.shares is None and taken) or cap - taken < need:
                continue
            candidates.append((cap - taken, device, need))
        if len(candidates) < option.count:
            return None
        candidates.sort()
        return [((driver, device), need) for _, device, need in candidates[: option.count]]

    def take_shares(self, take: ShareTake) -> None:
        used = {driver: dict(devices) for driver, devices in self.share_used.items()}
        for (driver, device), shares in take.items():
            per_driver = used.setdefault(driver, {})
            per_driver[device] = per_driver.get(device, 0) + shares
        self.share_used = used


@dataclass(frozen=True)
class PendingPod:
    namespace: str
    name: str
    requests: Resources
    node_selector: Mapping[str, str] = field(default_factory=dict)
    tolerations: Sequence[Toleration] = ()
    devices: Mapping[str, int] = field(default_factory=dict)  # "<DRA driver>/<slot>" → wanted
    shared_devices: Mapping[str, int] = field(default_factory=dict)  # DRA driver → devices shared
    extended: Mapping[str, int] = field(default_factory=dict)  # extended resource → count
    share_claims: Sequence[ShareClaim] = ()
    slots: Mapping[str, Decimal] = field(default_factory=dict)  # device slot → amount


@dataclass(frozen=True)
class PendingGroup:
    namespace: str
    name: str
    queue: str
    priority: int
    created_at: str
    min_member: int
    pods: Sequence[PendingPod]  # the members still to place
    required_levels: Sequence[str] = ()  # node labels every pod of the group shares a value of
    placed_members: int = 0  # members bound or with a bind in flight
    placed_nodes: Sequence[str] = ()  # nodes of those members


@dataclass
class QueueState:
    name: str
    limit: Resources | None  # None: no limit
    used: Resources = field(default_factory=Resources)
    parent: str | None = None
    fair_share_factor: float = 0.0  # higher goes first, as in the Manager's fair share
    slot_limits: Mapping[str, Decimal] = field(default_factory=dict)  # device slot → limit
    slot_used: Mapping[str, Decimal] = field(default_factory=dict)


def queue_chain(queues: Mapping[str, QueueState], name: str) -> list[QueueState]:
    """The queue and its ancestors; a cycle or a missing parent ends the chain."""
    chain: list[QueueState] = []
    current = queues.get(name)
    while current is not None and current not in chain:
        chain.append(current)
        current = queues.get(current.parent) if current.parent else None
    return chain


def add_slots(a: Mapping[str, Decimal], b: Mapping[str, Decimal]) -> dict[str, Decimal]:
    total = dict(a)
    for slot, amount in b.items():
        total[slot] = total.get(slot, Decimal(0)) + amount
    return total


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


def _fits(node: NodeState, pod: PendingPod) -> bool:
    return (
        _eligible(node, pod)
        and pod.requests.fits_in(node.free)
        and node.has_devices(pod.devices, pod.shared_devices)
        and node.has_extended(pod.extended)
        and (not pod.share_claims or node.fit_shares(pod.share_claims) is not None)
    )


def _choose(
    nodes: Sequence[NodeState], pod: PendingPod, strategy: PlacementStrategy
) -> NodeState | None:
    candidates = [n for n in nodes if _fits(n, pod)]
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
    """The first topology domain that takes every pod of the group; members already placed
    fix the domain."""
    levels = group.required_levels
    fixed = {n.name: n for n in nodes}
    joined = {
        tuple(fixed[name].labels.get(level) for level in levels)
        for name in group.placed_nodes
        if name in fixed
    }
    for domain in _domains(nodes, levels):
        if levels and joined and {tuple(domain[0].labels[lv] for lv in levels)} != joined:
            continue
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
        node.take_extended(pod.extended)
        if pod.share_claims:
            node.take_shares(node.fit_shares(pod.share_claims) or {})
        placed[pod.name] = node.name
    for original, tried in zip(nodes, trial, strict=True):
        original.used = tried.used
        original.devices_used = tried.devices_used
        original.extended_used = tried.extended_used
        original.share_used = tried.share_used
    return placed


def _empty(node: NodeState) -> NodeState:
    return replace(node, used=Resources(), devices_used={}, extended_used={}, share_used={})


def _would_fit_when_idle(
    nodes: Sequence[NodeState], group: PendingGroup, strategy: PlacementStrategy
) -> bool:
    return _place_gang([_empty(n) for n in nodes], group, strategy) is not None


def _over_limit(
    chain: Sequence[QueueState], demand: Resources, slots: Mapping[str, Decimal]
) -> QueueState | None:
    for q in chain:
        if q.limit is not None and not (q.used + demand).fits_in(q.limit):
            return q
        for slot, limit in q.slot_limits.items():
            wanted = slots.get(slot, Decimal(0))
            if wanted > 0 and q.slot_used.get(slot, Decimal(0)) + wanted > limit:
                return q
    return None


def schedule(
    nodes: Sequence[NodeState],
    queues: Mapping[str, QueueState],
    groups: Sequence[PendingGroup],
    strategy: PlacementStrategy = PlacementStrategy.CONCENTRATED,
    policy: GpuAllocationPolicy = GpuAllocationPolicy.DRA,
) -> list[Placement | Skip]:
    """Decide which pending groups start now: higher priority, then the queue with the higher
    fair share factor, then the oldest.

    The first group of a queue that does not fit now, but would on idle nodes, keeps the nodes
    it can use: later groups of that queue may only use other nodes, so it is not starved.
    """

    def order(g: PendingGroup) -> tuple[int, float, str, str]:
        queue = queues.get(g.queue)
        return (-g.priority, -(queue.fair_share_factor if queue else 0.0), g.created_at, g.name)

    heads: dict[str, tuple[PendingGroup, frozenset[str]]] = {}
    results: list[Placement | Skip] = []
    for group in sorted(groups, key=order):
        present = len(group.pods) + group.placed_members
        if present < group.min_member:
            results.append(
                Skip(
                    group,
                    SkipReason.WAITING_FOR_PODS,
                    f"{present} of {group.min_member} pods exist",
                )
            )
            continue
        if policy == GpuAllocationPolicy.DEVICE_PLUGIN and any(p.share_claims for p in group.pods):
            results.append(
                Skip(
                    group,
                    SkipReason.UNSUPPORTED,
                    "device shares need the dra GPU allocation policy",
                )
            )
            continue
        demand = Resources()
        slots: dict[str, Decimal] = {}
        for pod in group.pods:
            demand = demand + pod.requests
            slots = add_slots(slots, pod.slots)
        chain = queue_chain(queues, group.queue)
        full = _over_limit(chain, demand, slots)
        if full is not None:
            results.append(
                Skip(group, SkipReason.QUEUE_LIMIT, f"queue {full.name} is at its limit")
            )
            continue
        head = heads.get(group.queue)
        usable = nodes if head is None else [n for n in nodes if n.name not in head[1]]
        placed = _place_gang(usable, group, strategy)
        if placed is None:
            if head is not None and _place_gang([replace(n) for n in nodes], group, strategy):
                results.append(
                    Skip(
                        group,
                        SkipReason.RESERVED,
                        f"waiting behind {head[0].name}, which is first in queue {group.queue}",
                    )
                )
                continue
            if head is None and _would_fit_when_idle(nodes, group, strategy):
                keeps = frozenset(n.name for n in nodes if any(_eligible(n, p) for p in group.pods))
                heads[group.queue] = (group, keeps)
            results.append(
                Skip(group, SkipReason.UNSCHEDULABLE, "not every pod of the group fits now")
            )
            continue
        for q in chain:
            q.used = q.used + demand
            q.slot_used = add_slots(q.slot_used, slots)
        results.append(Placement(group, placed))
    return results
