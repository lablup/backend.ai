"""Value types for the ComputeBackend instance-lifecycle interface."""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, NewType

from ai.backend.agent.types import MountInfo, Port
from ai.backend.common.types import DeviceId, DeviceName, KernelId, SlotName

if TYPE_CHECKING:
    from ai.backend.agent.stats import Measurement

# Backend-native instance id (docker container id, k8s pod name, VM id).
InstanceId = NewType("InstanceId", str)


@dataclass(frozen=True)
class DeviceAllocation:
    """One compute-device allocation, resolved by ResourceService before instance creation."""

    device_name: DeviceName
    slot_name: SlotName
    device_id: DeviceId
    amount: Decimal


class NetworkMode(enum.StrEnum):
    BRIDGE = "bridge"
    OVERLAY = "overlay"
    HOST = "host"


@dataclass(frozen=True)
class NetworkRef:
    name: str
    mode: NetworkMode


@dataclass(frozen=True)
class InstanceAttachments:
    """Already-acquired side resources the backend applies at create; it never allocates/frees them."""

    mounts: Sequence[MountInfo] = ()
    device_allocations: Sequence[DeviceAllocation] = ()
    port_bindings: Sequence[Port] = ()
    network: NetworkRef | None = None


@dataclass(frozen=True)
class InstanceSpec:
    kernel_id: KernelId
    image: str
    labels: Mapping[str, str]
    environ: Mapping[str, str] = field(default_factory=dict)
    command: Sequence[str] | None = None
    attachments: InstanceAttachments = field(default_factory=InstanceAttachments)


@dataclass(frozen=True)
class InstanceHandle:
    """Operational reference to a created instance; kernel_id is the sole correlation key."""

    instance_id: InstanceId
    kernel_id: KernelId


class InstanceState(enum.StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    TERMINATING = "terminating"
    TERMINATED = "terminated"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class InstanceInfo:
    """Self-described instance snapshot, reconstructable from labels alone."""

    handle: InstanceHandle
    state: InstanceState
    image: str
    labels: Mapping[str, str]


@dataclass(frozen=True)
class InstanceStat:
    instance_id: InstanceId
    metrics: Mapping[str, Measurement] = field(default_factory=dict)
