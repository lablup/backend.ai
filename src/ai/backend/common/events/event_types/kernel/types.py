import enum
from typing import Optional, Self


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
    def from_value(cls, value: Optional[str]) -> Optional[Self]:
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            pass
        return None
