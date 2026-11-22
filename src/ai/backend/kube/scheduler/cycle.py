"""One scheduling cycle over a snapshot: ordering and gang placement. No API calls.

The Manager admits sessions (queues, fair share, resource policies); the cluster only places
the admitted groups, in order of priority, then of SessionWorkload creation.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Final

from ai.backend.kube.crd.device import GPUAllocationPolicy
from ai.backend.kube.crd.session import (
    SessionGroupAdmission,
    SessionGroupDirection,
    SessionGroupEnforcement,
)

if TYPE_CHECKING:
    from ai.backend.kube.scheduler.selection import NodeSelector


class SkipReason(enum.StrEnum):
    WAITING_FOR_PODS = "WaitingForPods"
    UNSCHEDULABLE = "Unschedulable"
    RESERVED = "WaitingForEarlierGroup"
    UNSUPPORTED = "Unsupported"
    WAITING_FOR_GROUP_MEMBERS = "WaitingForGroupMembers"
    GROUP_DOES_NOT_FIT = "GroupDoesNotFit"


_SHARES_UNSUPPORTED: Final = "device shares need the bai or nvidia-dra GPU allocation policy"


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


@dataclass(frozen=True)
class GroupPolicy:
    """The SessionGroup of a session and its placement policy (BEP-1064, BEP-1083)."""

    id: str
    direction: SessionGroupDirection = SessionGroupDirection.NONE
    enforcement: SessionGroupEnforcement = SessionGroupEnforcement.PREFERRED
    admission: SessionGroupAdmission = SessionGroupAdmission.INDEPENDENT
    member_count: int | None = None

    @property
    def all_or_none(self) -> bool:
        return self.admission == SessionGroupAdmission.ALL_OR_NONE


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
    # SessionGroup id → sessions of the group with a kernel on the node
    group_members: Mapping[str, frozenset[str]] = field(default_factory=dict)

    @property
    def free(self) -> Resources:
        return self.allocatable - self.used

    def member_count(self, group_id: str, session: str) -> int:
        """Other sessions of the group on the node: a session does not count against itself."""
        return len(self.group_members.get(group_id, frozenset()) - {session})

    def add_member(self, group_id: str, session: str) -> None:
        members = dict(self.group_members)
        members[group_id] = members.get(group_id, frozenset()) | {session}
        self.group_members = members

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
    """The kernels of one sokovan SessionWorkload, placed all or none."""

    namespace: str
    name: str  # of the SessionWorkload
    priority: int
    created_at: str  # of the SessionWorkload
    min_member: int
    pods: Sequence[PendingPod]  # the members still to place
    required_levels: Sequence[str] = ()  # node labels every pod of the group shares a value of
    placed_members: int = 0  # members bound or with a bind in flight
    placed_nodes: Sequence[str] = ()  # nodes of those members
    session_id: str | None = None
    session_group: GroupPolicy | None = None
    # Sessions of an all_or_none group whose SessionWorkload and every kernel Pod exist
    group_ready: int = 0

    @property
    def member(self) -> str:
        """The session as a member of its SessionGroup, as kernel Pods label it."""
        return self.session_id or f"{self.namespace}/{self.name}"

    @property
    def unit(self) -> str | None:
        """The all_or_none SessionGroup placed together with this session, if any."""
        group = self.session_group
        return group.id if group is not None and group.all_or_none else None


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
    nodes: Sequence[NodeState],
    pod: PendingPod,
    selector: NodeSelector,
    group: PendingGroup,
    world: Sequence[NodeState],
) -> NodeState | None:
    """The node the sokovan_core strategy picks among those the Pod fits on; `world` holds
    every node, for the SessionGroup members placed so far."""
    return selector.choose(
        [n for n in nodes if _fits(n, pod)],
        pod,
        group.session_id,
        group=group.session_group,
        member=group.member,
        world=world,
    )


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
    nodes: Sequence[NodeState],
    group: PendingGroup,
    selector: NodeSelector,
    world: Sequence[NodeState],
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
        placed = _place_in(domain, group, selector, world)
        if placed is not None:
            return placed
    return None


def _commit(original: NodeState, tried: NodeState) -> None:
    original.used = tried.used
    original.devices_used = tried.devices_used
    original.extended_used = tried.extended_used
    original.share_used = tried.share_used
    original.group_members = tried.group_members


def _place_in(
    nodes: Sequence[NodeState],
    group: PendingGroup,
    selector: NodeSelector,
    world: Sequence[NodeState],
) -> dict[str, str] | None:
    """Place every pod of the group on a tentative copy; nothing changes unless all fit."""
    trial = [replace(n) for n in nodes]
    tried = {n.name: n for n in trial}
    view = [tried.get(n.name, n) for n in world]
    placed: dict[str, str] = {}

    def size(p: PendingPod) -> tuple[int, int, int]:
        return (-sum(p.devices.values()), -p.requests.cpu_milli, -p.requests.memory)

    for pod in sorted(group.pods, key=size):
        node = _choose(trial, pod, selector, group, view)
        if node is None:
            return None
        node.used = node.used + pod.requests
        node.take_devices(pod.devices)
        node.take_extended(pod.extended)
        if pod.share_claims:
            node.take_shares(node.fit_shares(pod.share_claims) or {})
        if group.session_group is not None:
            node.add_member(group.session_group.id, group.member)
        placed[pod.name] = node.name
    for original, node in zip(nodes, trial, strict=True):
        _commit(original, node)
    return placed


def _empty(node: NodeState) -> NodeState:
    return replace(node, used=Resources(), devices_used={}, extended_used={}, share_used={})


def _place_unit(
    usable: Sequence[NodeState],
    world: Sequence[NodeState],
    unit: Sequence[PendingGroup],
    selector: NodeSelector,
) -> list[dict[str, str]] | None:
    """Place every session of the unit on tentative copies of `world`, in order; nothing
    changes unless all fit. Later sessions count the earlier ones as group members."""
    trial = [replace(n) for n in world]
    tried = {n.name: n for n in trial}
    usable_trial = [tried[n.name] for n in usable]
    placements = []
    for group in unit:
        placed = _place_gang(usable_trial, group, selector, trial)
        if placed is None:
            return None
        placements.append(placed)
    for original, node in zip(world, trial, strict=True):
        _commit(original, node)
    return placements


def _order(g: PendingGroup) -> tuple[int, str, str, str]:
    return (-g.priority, g.created_at, g.namespace, g.name)


def _units(groups: Sequence[PendingGroup]) -> list[list[PendingGroup]]:
    """Sessions in placement order; the pending sessions of an all_or_none SessionGroup form
    one unit, ordered by its highest priority, then its oldest SessionWorkload."""
    by_unit: dict[str, list[PendingGroup]] = {}
    units: list[list[PendingGroup]] = []
    for group in sorted(groups, key=_order):
        if group.unit is None:
            units.append([group])
        elif group.unit in by_unit:
            by_unit[group.unit].append(group)
        else:
            by_unit[group.unit] = [group]
            units.append(by_unit[group.unit])

    def key(unit: list[PendingGroup]) -> tuple[int, str, str, str]:
        return (
            -max(g.priority for g in unit),
            min(g.created_at for g in unit),
            unit[0].namespace,
            unit[0].name,
        )

    return sorted(units, key=key)


@dataclass
class _Cycle:
    """The state one `schedule` call carries from unit to unit."""

    nodes: Sequence[NodeState]
    selector: NodeSelector
    policy: GPUAllocationPolicy
    # The first unit that does not fit now but would on idle nodes, and the nodes it keeps
    head: tuple[PendingGroup, frozenset[str]] | None = None

    def usable(self) -> Sequence[NodeState]:
        if self.head is None:
            return self.nodes
        kept = self.head[1]
        return [n for n in self.nodes if n.name not in kept]

    def unsupported(self, unit: Sequence[PendingGroup]) -> bool:
        return self.policy == GPUAllocationPolicy.DEVICE_PLUGIN and any(
            p.share_claims for g in unit for p in g.pods
        )

    def blocked(self, unit: Sequence[PendingGroup]) -> str | None:
        """Why a unit that does not fit now waits behind the head; otherwise it becomes the
        head if it would fit on idle nodes, and None is returned."""
        if self.head is not None:
            copies = [replace(n) for n in self.nodes]
            if _place_unit(copies, copies, unit, self.selector) is None:
                return None
            head = self.head[0]
            return f"waiting behind {head.namespace}/{head.name}, which goes first"
        idle = [_empty(n) for n in self.nodes]
        if _place_unit(idle, idle, unit, self.selector) is not None:
            keeps = frozenset(
                n.name for n in self.nodes if any(_eligible(n, p) for g in unit for p in g.pods)
            )
            self.head = (unit[0], keeps)
        return None

    def one(self, group: PendingGroup) -> Placement | Skip:
        present = len(group.pods) + group.placed_members
        if present < group.min_member:
            return Skip(
                group, SkipReason.WAITING_FOR_PODS, f"{present} of {group.min_member} pods exist"
            )
        if self.unsupported([group]):
            return Skip(group, SkipReason.UNSUPPORTED, _SHARES_UNSUPPORTED)
        placed = _place_gang(self.usable(), group, self.selector, self.nodes)
        if placed is not None:
            return Placement(group, placed)
        if (message := self.blocked([group])) is not None:
            return Skip(group, SkipReason.RESERVED, message)
        return Skip(group, SkipReason.UNSCHEDULABLE, "not every pod of the group fits now")

    def all_or_none(
        self, unit: Sequence[PendingGroup], policy: GroupPolicy
    ) -> list[Placement | Skip]:
        def skip(reason: SkipReason, message: str) -> list[Placement | Skip]:
            return [Skip(g, reason, message) for g in unit]

        if policy.member_count is None:
            return skip(SkipReason.UNSUPPORTED, "all_or_none admission needs memberCount")
        ready = unit[0].group_ready
        incomplete = any(len(g.pods) + g.placed_members < g.min_member for g in unit)
        if ready < policy.member_count or incomplete:
            return skip(
                SkipReason.WAITING_FOR_GROUP_MEMBERS,
                f"{ready} of {policy.member_count} sessions of group {policy.id} have every"
                " kernel Pod",
            )
        if self.unsupported(unit):
            return skip(SkipReason.UNSUPPORTED, _SHARES_UNSUPPORTED)
        placements = _place_unit(self.usable(), self.nodes, unit, self.selector)
        if placements is not None:
            return [Placement(g, p) for g, p in zip(unit, placements, strict=True)]
        if (message := self.blocked(unit)) is not None:
            return skip(SkipReason.RESERVED, message)
        return skip(
            SkipReason.GROUP_DOES_NOT_FIT, f"not every session of group {policy.id} fits now"
        )


def schedule(
    nodes: Sequence[NodeState],
    groups: Sequence[PendingGroup],
    selector: NodeSelector,
    policy: GPUAllocationPolicy = GPUAllocationPolicy.BAI,
) -> list[Placement | Skip]:
    """Place the pending groups in order: higher priority, then the older SessionWorkload,
    then the name. An all_or_none SessionGroup places all its pending sessions or none.

    The first group that does not fit now, but would on idle nodes, keeps the nodes it can
    use: later groups may only use other nodes, so it is not starved.
    """
    cycle = _Cycle(nodes, selector, policy)
    results: list[Placement | Skip] = []
    for unit in _units(groups):
        group_policy = unit[0].session_group
        if group_policy is not None and group_policy.all_or_none:
            results.extend(cycle.all_or_none(unit, group_policy))
        else:
            results.append(cycle.one(unit[0]))
    return results
