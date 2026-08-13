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


class SlotOccupancy(BackendAISchema):
    """How much of one slot each individual device supplies."""

    amounts: Mapping[DeviceId, Decimal]


class DeviceOccupancy(BackendAISchema):
    """The slots one device supplies.

    A device supplies more than one slot when it is metered along more than one axis —
    `cuda` supplies both `cuda.device` and `cuda.shares`.
    """

    slots: Mapping[ResourceSlotName, SlotOccupancy]


class KernelOccupancy(BackendAISchema):
    """
    The resources the kernel occupies, attributed to the devices supplying them.

    `DeviceName` names a device (`cuda`) and `DeviceId` one of its units (`0`), so the
    two levels keyed by a device are not the same thing.
    """

    devices: Mapping[DeviceName, DeviceOccupancy]

    @property
    def slot_totals(self) -> list[ResourceSlotEntry]:
        """
        The per-device amounts summed per slot — what a caller records as occupancy.

        A slot supplied by no device is left out rather than reported as zero, which is
        the distinction a caller storing the result depends on.

        Not a `computed_field`: it would be written into the payload beside the
        occupancy it is derived from, and a receiver recomputes it anyway.
        """
        totals: list[ResourceSlotEntry] = []
        for device in self.devices.values():
            for slot_name, slot in device.slots.items():
                if not slot.amounts:
                    continue
                total = sum(slot.amounts.values(), Decimal(0))
                totals.append(ResourceSlotEntry(resource_type=slot_name, quantity=str(total)))
        return totals


class DeviceCapacity(BackendAISchema):
    """
    What a device reports about itself.

    Both are defaulted, unlike every other field here: the compute plugin's own
    `ComputedDeviceCapacity` declares them `NotRequired`, so a device that measures
    neither reports neither.
    """

    mem: int | None = None
    proc: int | None = None


class AttachedDevice(BackendAISchema):
    device_id: DeviceId
    model_name: str
    data: DeviceCapacity


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
    attached_devices: Mapping[DeviceName, list[AttachedDevice]]
    occupancy: KernelOccupancy
