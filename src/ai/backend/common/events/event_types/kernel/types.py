import enum
from collections.abc import Mapping
from decimal import Decimal
from typing import Self

from ai.backend.common.identifier.resource_slot import ResourceSlotName
from ai.backend.common.types import (
    BackendAISchema,
    ContainerId,
    DeviceId,
    DeviceName,
    ResourceSlotEntry,
    ServicePortProtocols,
)


class KernelLifecycleEventReason(enum.StrEnum):
    AGENT_TERMINATION = "agent-termination"
    ALREADY_TERMINATED = "already-terminated"
    ANOMALY_DETECTED = "anomaly-detected"
    EXEC_TIMEOUT = "exec-timeout"
    FAILED_TO_CREATE = "failed-to-create"
    FAILED_TO_START = "failed-to-start"
    FORCE_TERMINATED = "force-terminated"
    BOOTSTRAP_TIMEOUT = "bootstrap-timeout"
    HANG_TIMEOUT = "hang-timeout"
    IDLE_TIMEOUT = "idle-timeout"
    IDLE_SESSION_LIFETIME = "idle-session-lifetime"
    IDLE_UTILIZATION = "idle-utilization"
    KILLED_BY_EVENT = "killed-by-event"
    SERVICE_SCALED_DOWN = "service-scaled-down"
    NEW_CONTAINER_STARTED = "new-container-started"
    PENDING_TIMEOUT = "pending-timeout"
    RESTARTING = "restarting"
    RESTART_TIMEOUT = "restart-timeout"
    RESUMING_AGENT_OPERATION = "resuming-agent-operation"
    SELF_TERMINATED = "self-terminated"
    TASK_FAILED = "task-failed"
    TASK_TIMEOUT = "task-timeout"
    TASK_CANCELLED = "task-cancelled"
    TASK_FINISHED = "task-finished"
    TERMINATED_UNKNOWN_CONTAINER = "terminated-unknown-container"
    UNKNOWN = "unknown"
    USER_REQUESTED = "user-requested"
    USER_PURGED = "user-purged"
    NOT_FOUND_IN_MANAGER = "not-found-in-manager"
    CONTAINER_NOT_FOUND = "container-not-found"

    @classmethod
    def from_value(cls, value: str | None) -> Self | None:
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            pass
        return None


class UsedDevice(BackendAISchema):
    """
    One device unit the kernel holds, and how much of it.

    `used` is in the scheduler's units — the slots it accounts by, of which a unit
    supplies more than one when it is metered along more than one axis, as a `cuda`
    device does with `cuda.device` and `cuda.shares`. `processing_units` and
    `memory_size` are that same amount in the device's own units, mirroring
    `AbstractComputeDevice`; only an accelerator reports them.
    """

    model_name: str | None  # kept for the GPU usage stats, which aggregate device models
    used: Mapping[ResourceSlotName, Decimal]
    processing_units: int | None
    memory_size: int | None


class UsedDevices(BackendAISchema):
    """
    The devices the kernel uses.

    Keyed by device name (`cuda`) and then by unit (`0`): `DeviceName` names a kind of
    device, `DeviceId` one of its units.
    """

    units: Mapping[DeviceName, Mapping[DeviceId, UsedDevice]]

    @property
    def slot_totals(self) -> list[ResourceSlotEntry]:
        """
        The per-unit amounts summed per slot — what a caller records as the kernel's usage.

        Not a `computed_field`: it would be written into the payload beside the amounts
        it is derived from, where nothing reads it — a receiver recomputes it — and it
        can disagree with the value next to it.
        """
        totals: dict[ResourceSlotName, Decimal] = {}
        for units in self.units.values():
            for device in units.values():
                for slot_name, amount in device.used.items():
                    totals[slot_name] = totals.get(slot_name, Decimal(0)) + amount
        return [
            ResourceSlotEntry(resource_type=slot_name, quantity=str(total))
            for slot_name, total in totals.items()
        ]


class ServicePortInfo(BackendAISchema):
    name: str
    protocol: ServicePortProtocols
    container_ports: list[int]
    host_ports: list[int | None]
    is_inference: bool


class KernelCreationInfo(BackendAISchema):
    """
    What the agent reports about a kernel once its container is up.

    This is the contract with the manager, not a rendering of the agent's own resource
    spec: it carries the facts the manager records against the kernel and nothing else.
    """

    container_id: ContainerId
    kernel_host: str
    repl_in_port: int
    repl_out_port: int
    service_ports: list[ServicePortInfo]
    used_devices: UsedDevices
