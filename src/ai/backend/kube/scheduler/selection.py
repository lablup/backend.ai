"""Node selection through the sokovan_core agent selectors: a node is an agent.

`kube/scheduler/cycle.py` keeps what only the cluster knows (taints, node selectors, DRA
devices, shares, extended resources, topology, gangs) and passes the nodes that fit a Pod to the
strategy the Manager uses for agents (concentrated, dispersed, roundrobin), after the
sokovan_core filters that apply to nodes (architecture, remaining slots).
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import TYPE_CHECKING, Final
from uuid import UUID

from ai.backend.common.data.entity.resource_group import ResourceGroupID
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.data.entity.session_group import SessionGroupID
from ai.backend.common.types import AgentId, AgentSelectionStrategy, ArchName, SessionId
from ai.backend.sokovan_core.selectors.concentrated import ConcentratedAgentSelector
from ai.backend.sokovan_core.selectors.dispersed import DispersedAgentSelector
from ai.backend.sokovan_core.selectors.filters.exclusion.architecture import (
    ArchitectureTrackerFilter,
)
from ai.backend.sokovan_core.selectors.filters.exclusion.session_group_strict import (
    SessionGroupStrictTrackerFilter,
)
from ai.backend.sokovan_core.selectors.filters.stateful.resource import ResourceTrackerFilter
from ai.backend.sokovan_core.selectors.orders.session_group import SessionGroupOrder
from ai.backend.sokovan_core.selectors.roundrobin import RoundRobinAgentSelector
from ai.backend.sokovan_core.selectors.selector import AbstractAgentSelector, AgentSelectionCriteria
from ai.backend.sokovan_core.selectors.tracker import AgentStateTracker
from ai.backend.sokovan_core.selectors.types import ResourceRequirements
from ai.backend.sokovan_core.types.agent import AgentInfo, AgentLimit, AgentResource, SlotResource
from ai.backend.sokovan_core.types.policy import (
    AgentSelectionPolicy,
    SessionGroupPlacementDirection,
    SessionGroupPlacementEnforcement,
)
from ai.backend.sokovan_core.types.workload import ResourceRequest, SessionGroupPolicy

if TYPE_CHECKING:
    from ai.backend.kube.scheduler.cycle import GroupPolicy, NodeState, PendingPod

ARCH_LABEL: Final = "kubernetes.io/arch"
CPU_SLOT: Final = "cpu"
MEM_SLOT: Final = "mem"
SELECTABLE_STRATEGIES: Final = (
    AgentSelectionStrategy.CONCENTRATED,
    AgentSelectionStrategy.DISPERSED,
    AgentSelectionStrategy.ROUNDROBIN,
)
_NO_ID: Final = UUID(int=0)
_NO_LIMIT: Final = AgentLimit(max_container_count=None)
_SHARES_PREFIX: Final = "shares:"


def node_slots(node: NodeState) -> dict[str, tuple[Decimal, Decimal]]:
    """Slot name → (capacity, used) of a node; used never exceeds the capacity."""
    slots: dict[str, tuple[Decimal, Decimal]] = {
        CPU_SLOT: (Decimal(node.allocatable.cpu_milli) / 1000, Decimal(node.used.cpu_milli) / 1000),
        MEM_SLOT: (Decimal(node.allocatable.memory), Decimal(node.used.memory)),
    }
    for key, count in node.devices.items():  # by "<driver>" and by "<driver>/<slot>"
        slots[key] = (Decimal(count), Decimal(node.devices_used.get(key, 0)))
    for name, count in node.extended.items():
        slots[name] = (Decimal(count), Decimal(node.extended_used.get(name, 0)))
    for driver, capacities in node.share_capacity.items():
        used = node.share_used.get(driver) or {}
        slots[_SHARES_PREFIX + driver] = (
            Decimal(sum(capacities.values())),
            Decimal(sum(used.get(device, 0) for device in capacities)),
        )
    return {name: (cap, min(used, cap)) for name, (cap, used) in slots.items()}


def node_agent(node: NodeState) -> AgentInfo:
    """The node as the agent the sokovan_core selectors see."""
    return AgentInfo(
        agent_id=AgentId(node.name),
        agent_addr=node.name,
        architecture=ArchName(node.labels.get(ARCH_LABEL, "")),
        resources=AgentResource(
            slots={
                ResourceSlotName(name): SlotResource(capacity=cap, reserved=Decimal(0), used=used)
                for name, (cap, used) in node_slots(node).items()
            }
        ),
        container_count=node.used.pods,
    )


def pod_request(pod: PendingPod, slot_names: Sequence[str]) -> ResourceRequest:
    """The slots a Pod takes; every other slot of the pool is asked as zero, so the strategies
    keep devices it does not use free, as for agents. Shares and shared devices are checked
    per device by the cycle and left out here."""
    shared = {driver for driver in pod.shared_devices}
    shared |= {request.driver for claim in pod.share_claims for request in claim}
    slots: dict[str, Decimal] = {name: Decimal(0) for name in slot_names}
    for name in slot_names:
        driver = name.removeprefix(_SHARES_PREFIX).split("/", 1)[0]
        if driver in shared:
            del slots[name]
    slots[CPU_SLOT] = Decimal(pod.requests.cpu_milli) / 1000
    slots[MEM_SLOT] = Decimal(pod.requests.memory)
    for key, count in pod.devices.items():
        slots[key] = Decimal(count)
    for name, count in pod.extended.items():
        slots[name] = Decimal(count)
    return ResourceRequest(slots={ResourceSlotName(k): v for k, v in slots.items()})


def group_policy(group: GroupPolicy | None) -> SessionGroupPolicy | None:
    """The SessionGroup policy as the sokovan_core selectors take it; None without one."""
    if group is None:
        return None
    try:
        group_id = SessionGroupID(UUID(group.id))
    except ValueError:
        return None
    return SessionGroupPolicy(
        group_id=group_id,
        direction=SessionGroupPlacementDirection(group.direction),
        enforcement=SessionGroupPlacementEnforcement(group.enforcement),
    )


class NodeSelector:
    """Picks one of the nodes that fit a Pod with a sokovan_core strategy; other strategies
    fall back to concentrated, as in the Manager's strategy pool. A SessionGroup applies
    first, per node: strict as a filter, then preferred as an order (BEP-1064)."""

    _strategy: AgentSelectionStrategy
    _roundrobin: RoundRobinAgentSelector
    _architecture: ArchitectureTrackerFilter
    _resources: ResourceTrackerFilter
    _group_strict: SessionGroupStrictTrackerFilter
    _group_order: SessionGroupOrder

    def __init__(self, strategy: AgentSelectionStrategy) -> None:
        self._strategy = strategy
        # Kept across cycles: its turn advances with every selection.
        self._roundrobin = RoundRobinAgentSelector()
        self._architecture = ArchitectureTrackerFilter()
        self._resources = ResourceTrackerFilter()
        self._group_strict = SessionGroupStrictTrackerFilter()
        self._group_order = SessionGroupOrder()

    @property
    def strategy(self) -> AgentSelectionStrategy:
        return self._strategy

    def choose(
        self,
        candidates: Sequence[NodeState],
        pod: PendingPod,
        session_id: str | None = None,
        *,
        group: GroupPolicy | None = None,
        member: str = "",
        world: Sequence[NodeState] = (),
    ) -> NodeState | None:
        """One of `candidates` (nodes the Pod fits on), or None if the filters drop them all.
        `world` is every node: the strict filter keeps its pack anchor over all of them, and
        `member` (the session) does not count as a member of its own group."""
        if not candidates:
            return None
        by_name = {node.name: node for node in candidates}
        slot_names = sorted({name for node in candidates for name in node_slots(node)})
        request = pod_request(pod, slot_names)
        arch = pod.node_selector.get(ARCH_LABEL)
        requirement = ResourceRequirements(
            requested_slots=request,
            required_architecture=ArchName(arch or ""),
            container_count=1,
        )
        criteria = AgentSelectionCriteria(
            session_id=SessionId(_uuid(session_id)),
            resource_group_id=ResourceGroupID(_NO_ID),
            requirements=[requirement],
            agent_selection_policy=AgentSelectionPolicy.PREFERRED,
            designated_agent_ids=None,
            job_priority=0,
            victim_candidates=None,
            session_group=group_policy(group),
        )

        def tracker(node: NodeState) -> AgentStateTracker:
            counts = {}
            if criteria.session_group is not None and group is not None:
                counts[criteria.session_group.group_id] = node.member_count(group.id, member)
            return AgentStateTracker(original_agent=node_agent(node), group_member_counts=counts)

        trackers: Sequence[AgentStateTracker] = [tracker(node) for node in candidates]
        if criteria.session_group is not None:
            conforming = {
                str(t.original_agent.agent_id)
                for t in self._group_strict.filter(
                    [tracker(node) for node in world or candidates], criteria, requirement
                )
            }
            trackers = [t for t in trackers if str(t.original_agent.agent_id) in conforming]
        if arch:
            trackers = self._architecture.filter(trackers, criteria, requirement)
        trackers = self._resources.filter(trackers, criteria, requirement, _NO_LIMIT)
        if not trackers:
            return None
        best = min(self._group_order.rank(t, criteria) for t in trackers)
        trackers = [t for t in trackers if self._group_order.rank(t, criteria) == best]
        picked = self._selector(request).select_tracker_by_strategy(trackers, requirement)
        return by_name[str(picked.original_agent.agent_id)]

    def _selector(self, request: ResourceRequest) -> AbstractAgentSelector:
        # Devices first, then CPU and memory: a device Pod fills (or spreads over) device
        # nodes by their devices, as the Manager's priority puts accelerators first.
        priority = [str(s) for s in sorted(request.slots) if s not in (CPU_SLOT, MEM_SLOT)]
        priority += [CPU_SLOT, MEM_SLOT]
        match self._strategy:
            case AgentSelectionStrategy.DISPERSED:
                return DispersedAgentSelector(priority)
            case AgentSelectionStrategy.ROUNDROBIN:
                return self._roundrobin
            case _:
                return ConcentratedAgentSelector(priority)


def _uuid(value: str | None) -> UUID:
    try:
        return UUID(value) if value else _NO_ID
    except ValueError:
        return _NO_ID
