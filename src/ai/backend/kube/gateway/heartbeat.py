"""Register the cluster with the Manager as one agent: the session gateway.

Kernel RPCs reach the gateway through this agent's address. Its slots are the capacity of
the nodes sessions can use; the cluster's sokovan places the Pods.
"""

from __future__ import annotations

import asyncio
import logging
import platform
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from importlib.resources import files
from typing import Any, Final

from kubernetes_asyncio import client
from kubernetes_asyncio.client.exceptions import ApiException

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.data.entity.resource_slot import ResourceSlotName
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.event_types.agent.anycast import (
    AgentHeartbeatEvent,
    AgentStartedEvent,
)
from ai.backend.common.types import ResourceSlotEntry, SlotTypes
from ai.backend.kube.controller.devices import device_key
from ai.backend.kube.crd.base import CRD_VERSION
from ai.backend.kube.crd.device import DeviceProfile, DeviceProfileSpec, SharingMode
from ai.backend.kube.scheduler.counters import without_counter_blocked_devices
from ai.backend.kube.scheduler.cycle import NodeState
from ai.backend.kube.scheduler.snapshot import DEDICATED_TAINT_KEY, build_nodes, is_dedicated
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

HEARTBEAT_INTERVAL: Final = 10.0
MAX_NODE_SHAPES: Final = 256
# `AgentInfo.node_shapes` (contract C12) is added by the Manager side; sent once it exists.
_NODE_SHAPES_FIELD: Final = "node_shapes"
_ARCH_ALIASES: Final = {"amd64": "x86_64", "arm64": "aarch64"}
_DP = DeviceProfile.crd
_REPORTED_MODES: Final = frozenset({
    SharingMode.EXCLUSIVE,
    SharingMode.PARTITION,
    SharingMode.FRACTION,
})


def _slot_type(profile: DeviceProfileSpec) -> SlotTypes:
    """A MIG instance is a `UNIQUE` slot, as the Agent reports it."""
    return SlotTypes.UNIQUE if profile.sharing_mode == SharingMode.PARTITION else SlotTypes.COUNT


@dataclass(frozen=True)
class GatewayIdentity:
    resource_group: str
    advertised_addr: str  # tcp://host:port the Manager connects to
    public_key: bytes
    region: str | None = None


@dataclass(frozen=True)
class ClusterCapacity:
    slots: list[ResourceSlotEntry]  # summed over the counted nodes
    node_shapes: list[dict[str, str]]  # distinct allocatable shapes of the counted nodes


def _counted(node: NodeState, dedicated_only: bool = False) -> bool:
    """A node a session Pod can land on (the sokovan dedicated taint is tolerated by session
    Pods; `dedicated_only`: sokovan's binder places Pods only on nodes with it). `schedulable`
    already leaves out unready, cordoned and to-be-recycled nodes."""
    if dedicated_only and not is_dedicated(node):
        return False
    blocked = any(
        t.effect in ("NoSchedule", "NoExecute") and t.key != DEDICATED_TAINT_KEY
        for t in node.taints
    )
    return node.schedulable and not blocked


def _node_slots(node: NodeState, profiles: Sequence[DeviceProfileSpec]) -> dict[str, Decimal]:
    """CPU cores, memory, and per DeviceProfile slot: device shares (fraction) or devices (a
    whole GPU, a MIG instance, or a device plugin's extended resource)."""
    slots = {
        "cpu": Decimal(node.allocatable.cpu_milli) / 1000,
        "mem": Decimal(node.allocatable.memory),
    }
    for profile in profiles:
        if profile.sharing_mode not in _REPORTED_MODES:
            continue
        extended_name = profile.extended_resource_name
        if profile.sharing_mode == SharingMode.FRACTION:
            capacities = node.share_capacity.get(profile.driver_name) or {}
            amount = Decimal(sum(capacities.values())) / 100
        elif extended_name:
            amount = Decimal(node.extended.get(extended_name, 0))
        else:
            amount = Decimal(node.devices.get(device_key(profile), 0))
        slots[profile.slot_name] = slots.get(profile.slot_name, Decimal(0)) + amount
    return slots


def _decimal(value: Decimal) -> str:
    return str(value.normalize()) if value != value.to_integral_value() else str(int(value))


def cluster_capacity(
    nodes: Sequence[Mapping[str, Any]],
    resource_slices: Sequence[Mapping[str, Any]] = (),
    profiles: Sequence[DeviceProfileSpec] = (),
    resource_claims: Sequence[Mapping[str, Any]] = (),
    *,
    dedicated_only: bool = False,
) -> ClusterCapacity:
    """The slots of the nodes a session Pod can land on, in total and per distinct node.
    A device whose shared counters are taken by others counts as absent (a MIG slot: the held
    placements plus those that still fit, each alone); admission is optimistic."""
    resource_slices = without_counter_blocked_devices(resource_slices, resource_claims)
    totals: dict[str, Decimal] = {"cpu": Decimal(0), "mem": Decimal(0)}
    for profile in profiles:
        if profile.sharing_mode in _REPORTED_MODES:
            totals.setdefault(profile.slot_name, Decimal(0))
    shapes: dict[tuple[tuple[str, str], ...], dict[str, str]] = {}
    for node in build_nodes(nodes, [], resource_slices):
        if not _counted(node, dedicated_only):
            continue
        slots = _node_slots(node, profiles)
        for name, amount in slots.items():
            totals[name] += amount
        shape = {name: _decimal(amount) for name, amount in slots.items()}
        key = tuple(sorted(shape.items()))
        if key not in shapes and len(shapes) < MAX_NODE_SHAPES:
            shapes[key] = shape
    entries = [
        ResourceSlotEntry(resource_type=ResourceSlotName(name), quantity=_decimal(amount))
        for name, amount in totals.items()
    ]
    return ClusterCapacity(slots=entries, node_shapes=list(shapes.values()))


class GatewayHeartbeat:
    _api: client.ApiClient
    _core: client.CoreV1Api
    _custom: client.CustomObjectsApi
    _producer: EventProducer
    _identity: GatewayIdentity
    _dedicated_only: bool

    def __init__(
        self,
        api: client.ApiClient,
        producer: EventProducer,
        identity: GatewayIdentity,
        *,
        dedicated_only: bool = False,
    ) -> None:
        self._api = api
        self._core = client.CoreV1Api(api)
        self._custom = client.CustomObjectsApi(api)
        self._producer = producer
        self._identity = identity
        self._dedicated_only = dedicated_only

    async def run(self) -> None:
        started = False
        while True:
            try:
                await self.beat()
                if not started:
                    await self._producer.anycast_event(AgentStartedEvent(reason="self-started"))
                    log.info("gateway registered", resource_group=self._identity.resource_group)
                    started = True
            except (ApiException, OSError) as e:
                log.warning("gateway heartbeat failed", exc_info=e)
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    async def beat(self) -> None:
        nodes, slices, listed_profiles, claims = await asyncio.gather(
            self._core.list_node(),
            self._custom.list_cluster_custom_object("resource.k8s.io", "v1", "resourceslices"),
            self._custom.list_cluster_custom_object(_DP.group, CRD_VERSION, _DP.plural),
            self._custom.list_cluster_custom_object("resource.k8s.io", "v1", "resourceclaims"),
        )
        raw_nodes = [self._api.sanitize_for_serialization(n) for n in nodes.items]
        profiles = [DeviceProfile.model_validate(p).spec for p in listed_profiles["items"]]
        capacity = cluster_capacity(
            raw_nodes,
            slices["items"],
            profiles,
            claims["items"],
            dedicated_only=self._dedicated_only,
        )
        extra: dict[str, Any] = {}
        if _NODE_SHAPES_FIELD in AgentInfo.model_fields:
            extra[_NODE_SHAPES_FIELD] = capacity.node_shapes
        host = self._identity.advertised_addr.removeprefix("tcp://").rsplit(":", 1)[0]
        info = AgentInfo(
            ip=host,
            region=self._identity.region,
            scaling_group=self._identity.resource_group,
            addr=self._identity.advertised_addr,
            public_key=PublicKey(self._identity.public_key),
            public_host=host,
            available_resource_slots=capacity.slots,
            slot_key_and_units={
                ResourceSlotName("cpu"): SlotTypes.COUNT,
                ResourceSlotName("mem"): SlotTypes.BYTES,
                **{ResourceSlotName(p.slot_name): _slot_type(p) for p in profiles},
            },
            version=files("ai.backend.kube").joinpath("VERSION").read_text().strip(),
            compute_plugins={},
            architecture=_ARCH_ALIASES.get(platform.machine(), platform.machine()),
            auto_terminate_abusing_kernel=False,
            **extra,
        )
        await self._producer.anycast_event(AgentHeartbeatEvent(agent_info=info))
