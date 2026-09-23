import enum
from typing import Self


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
    ROUTE_TERMINATION = "route-termination"
    DRY_RUN_COMPLETE = "dry-run-complete"
    PREEMPTED_BY_SCHEDULER = "preempted-by-scheduler"
    AGENT_RESOURCE_GROUP_CHANGED = "agent-resource-group-changed"
    STALE_KERNEL = "stale-kernel"
    EXCEEDED_MAX_RETRIES = "exceeded-max-retries"
    ABNORMAL_TERMINATION = "abnormal-termination"
    RESCHEDULED = "rescheduled"
    TRIGGERED_BY_SCHEDULER = "triggered-by-scheduler"
    PASSED_PRECONDITIONS = "passed-preconditions"
    DEPRIORITIZED_FOR_RESCHEDULING = "deprioritized-for-rescheduling"
    PREEMPTION_RESERVATION = "preemption-reservation"
    PREEMPTED_BY_RESERVATION = "preempted-by-reservation"
    KERNEL_HANDLER_FAILURE = "kernel-handler-failure"

    @classmethod
    def from_value(cls, value: str | None) -> Self | None:
        if value is None:
            return None
        try:
            return cls(value)
        except ValueError:
            pass
        return None
