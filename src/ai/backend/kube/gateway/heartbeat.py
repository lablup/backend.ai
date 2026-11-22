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
from ai.backend.kube.scheduler.snapshot import DEDICATED_TAINT_KEY, build_nodes, is_dedicated
from ai.backend.logging.structured import StructuredLogger

log = StructuredLogger(logging.getLogger(__spec__.name))

HEARTBEAT_INTERVAL: Final = 10.0
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


def cluster_slots(
    nodes: Sequence[Mapping[str, Any]],
    resource_slices: Sequence[Mapping[str, Any]] = (),
    profiles: Sequence[DeviceProfileSpec] = (),
    *,
    dedicated_only: bool = False,
) -> list[ResourceSlotEntry]:
    """CPU cores, memory, whole devices and device shares of the nodes a session Pod can land
    on (the sokovan dedicated taint is tolerated by session Pods). `dedicated_only`: sokovan's
    binder places Pods only on nodes with that taint."""
    cpu = Decimal(0)
    mem = 0
    devices: dict[str, int] = {}
    shares: dict[str, int] = {}  # driver → 0.01-share units
    extended: dict[str, int] = {}
    for node in build_nodes(nodes, [], resource_slices):
        blocked = any(
            t.effect in ("NoSchedule", "NoExecute") and t.key != DEDICATED_TAINT_KEY
            for t in node.taints
        )
        if dedicated_only and not is_dedicated(node):
            continue
        if node.schedulable and not blocked:
            cpu += Decimal(node.allocatable.cpu_milli) / 1000
            mem += node.allocatable.memory
            for driver, count in node.devices.items():
                devices[driver] = devices.get(driver, 0) + count
            for driver, capacities in node.share_capacity.items():
                shares[driver] = shares.get(driver, 0) + sum(capacities.values())
            for name, count in node.extended.items():
                extended[name] = extended.get(name, 0) + count
    entries = [
        ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity=str(cpu.normalize())),
        ResourceSlotEntry(resource_type=ResourceSlotName("mem"), quantity=str(mem)),
    ]
    for profile in profiles:
        if profile.sharing_mode not in _REPORTED_MODES:
            continue
        # A fraction slot counts shares (a device holds its own share capacity); the others
        # count devices: a whole GPU, a MIG instance, or a device plugin's extended resource.
        extended_name = profile.extended_resource_name
        if profile.sharing_mode == SharingMode.FRACTION:
            quantity = str((Decimal(shares.get(profile.driver_name, 0)) / 100).normalize())
        elif extended_name:
            quantity = str(extended.get(extended_name, 0))
        else:
            quantity = str(devices.get(device_key(profile), 0))
        entries.append(
            ResourceSlotEntry(resource_type=ResourceSlotName(profile.slot_name), quantity=quantity)
        )
    return entries


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
        nodes, slices, listed_profiles = await asyncio.gather(
            self._core.list_node(),
            self._custom.list_cluster_custom_object("resource.k8s.io", "v1", "resourceslices"),
            self._custom.list_cluster_custom_object(_DP.group, CRD_VERSION, _DP.plural),
        )
        raw_nodes = [self._api.sanitize_for_serialization(n) for n in nodes.items]
        profiles = [DeviceProfile.model_validate(p).spec for p in listed_profiles["items"]]
        slots = cluster_slots(
            raw_nodes, slices["items"], profiles, dedicated_only=self._dedicated_only
        )
        host = self._identity.advertised_addr.removeprefix("tcp://").rsplit(":", 1)[0]
        info = AgentInfo(
            ip=host,
            region=self._identity.region,
            scaling_group=self._identity.resource_group,
            addr=self._identity.advertised_addr,
            public_key=PublicKey(self._identity.public_key),
            public_host=host,
            available_resource_slots=slots,
            slot_key_and_units={
                ResourceSlotName("cpu"): SlotTypes.COUNT,
                ResourceSlotName("mem"): SlotTypes.BYTES,
                **{ResourceSlotName(p.slot_name): _slot_type(p) for p in profiles},
            },
            version=files("ai.backend.kube").joinpath("VERSION").read_text().strip(),
            compute_plugins={},
            architecture=_ARCH_ALIASES.get(platform.machine(), platform.machine()),
            auto_terminate_abusing_kernel=False,
        )
        await self._producer.anycast_event(AgentHeartbeatEvent(agent_info=info))
