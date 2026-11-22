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
from ai.backend.kube.scheduler.snapshot import build_nodes
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
) -> list[ResourceSlotEntry]:
    """CPU cores, memory and whole devices of the nodes a session Pod can land on."""
    cpu = Decimal(0)
    mem = 0
    devices: dict[str, int] = {}
    for node in build_nodes(nodes, [], resource_slices):
        blocked = any(t.effect in ("NoSchedule", "NoExecute") for t in node.taints)
        if node.schedulable and not blocked:
            cpu += Decimal(node.allocatable.cpu_milli) / 1000
            mem += node.allocatable.memory
            for driver, count in node.devices.items():
                devices[driver] = devices.get(driver, 0) + count
    entries = [
        ResourceSlotEntry(resource_type=ResourceSlotName("cpu"), quantity=str(cpu.normalize())),
        ResourceSlotEntry(resource_type=ResourceSlotName("mem"), quantity=str(mem)),
    ]
    for profile in profiles:
        # One unit of a slot is one device: a whole GPU, a MIG instance, or (fraction) the
        # devices it is split from.
        key = (
            profile.driver_name
            if profile.sharing_mode == SharingMode.FRACTION
            else device_key(profile)
        )
        if profile.sharing_mode in _REPORTED_MODES:
            entries.append(
                ResourceSlotEntry(
                    resource_type=ResourceSlotName(profile.slot_name),
                    quantity=str(devices.get(key, 0)),
                )
            )
    return entries


class GatewayHeartbeat:
    _api: client.ApiClient
    _core: client.CoreV1Api
    _custom: client.CustomObjectsApi
    _producer: EventProducer
    _identity: GatewayIdentity

    def __init__(
        self, api: client.ApiClient, producer: EventProducer, identity: GatewayIdentity
    ) -> None:
        self._api = api
        self._core = client.CoreV1Api(api)
        self._custom = client.CustomObjectsApi(api)
        self._producer = producer
        self._identity = identity

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
        slots = cluster_slots(raw_nodes, slices["items"], profiles)
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
