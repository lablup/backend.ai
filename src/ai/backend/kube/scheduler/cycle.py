"""One scheduling cycle over a snapshot: ordering and gang placement. No API calls.

The Manager admits sessions (queues, fair share, resource policies); the cluster only places
the admitted groups, in order of priority, then of SessionWorkload creation.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from ai.backend.kube.crd.device import GPUAllocationPolicy

if TYPE_CHECKING:
    from ai.backend.kube.scheduler.selection import NodeSelector


class SkipReason(enum.StrEnum):
    WAITING_FOR_PODS = "WaitingForPods"
    UNSCHEDULABLE = "Unschedulable"
    RESERVED = "WaitingForEarlierGroup"
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


@dataclass(frozen=True)
class PendingGroup:
    namespace: str
    name: str
    priority: int
    created_at: str  # of the SessionWorkload (of the PodGroup when it is not known)
    min_member: int
    pods: Sequence[PendingPod]  # the members still to place
    required_levels: Sequence[str] = ()  # node labels every pod of the group shares a value of
    placed_members: int = 0  # members bound or with a bind in flight
    placed_nodes: Sequence[str] = ()  # nodes of those members
    session_id: str | None = None


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
    nodes: Sequence[NodeState], pod: PendingPod, selector: NodeSelector, session_id: str | None
) -> NodeState | None:
    """The node the sokovan_core strategy picks among those the Pod fits on."""
    return selector.choose([n for n in nodes if _fits(n, pod)], pod, session_id)


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
    nodes: Sequence[NodeState], group: PendingGroup, selector: NodeSelector
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
        placed = _place_in(domain, group, selector)
        if placed is not None:
            return placed
    return None


def _place_in(
    nodes: Sequence[NodeState], group: PendingGroup, selector: NodeSelector
) -> dict[str, str] | None:
    """Place every pod of the group on a tentative copy; nothing changes unless all fit."""
    trial = [replace(n) for n in nodes]
    placed: dict[str, str] = {}

    def size(p: PendingPod) -> tuple[int, int, int]:
        return (-sum(p.devices.values()), -p.requests.cpu_milli, -p.requests.memory)

    for pod in sorted(group.pods, key=size):
        node = _choose(trial, pod, selector, group.session_id)
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
    nodes: Sequence[NodeState], group: PendingGroup, selector: NodeSelector
) -> bool:
    return _place_gang([_empty(n) for n in nodes], group, selector) is not None


def schedule(
    nodes: Sequence[NodeState],
    groups: Sequence[PendingGroup],
    selector: NodeSelector,
    policy: GPUAllocationPolicy = GPUAllocationPolicy.BAI,
) -> list[Placement | Skip]:
    """Place the pending groups in order: higher priority, then the older SessionWorkload,
    then the name.

    The first group that does not fit now, but would on idle nodes, keeps the nodes it can
    use: later groups may only use other nodes, so it is not starved.
    """

    def order(g: PendingGroup) -> tuple[int, str, str, str]:
        return (-g.priority, g.created_at, g.namespace, g.name)

    head: tuple[PendingGroup, frozenset[str]] | None = None
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
        if policy == GPUAllocationPolicy.DEVICE_PLUGIN and any(p.share_claims for p in group.pods):
            results.append(
                Skip(
                    group,
                    SkipReason.UNSUPPORTED,
                    "device shares need the bai or nvidia-dra GPU allocation policy",
                )
            )
            continue
        usable = nodes if head is None else [n for n in nodes if n.name not in head[1]]
        placed = _place_gang(usable, group, selector)
        if placed is None:
            if head is not None and _place_gang([replace(n) for n in nodes], group, selector):
                results.append(
                    Skip(
                        group,
                        SkipReason.RESERVED,
                        f"waiting behind {head[0].namespace}/{head[0].name}, which goes first",
                    )
                )
                continue
            if head is None and _would_fit_when_idle(nodes, group, selector):
                keeps = frozenset(n.name for n in nodes if any(_eligible(n, p) for p in group.pods))
                head = (group, keeps)
            results.append(
                Skip(group, SkipReason.UNSCHEDULABLE, "not every pod of the group fits now")
            )
            continue
        results.append(Placement(group, placed))
    return results
