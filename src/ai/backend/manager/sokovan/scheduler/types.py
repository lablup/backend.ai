from __future__ import annotations

from enum import StrEnum


class ScheduleType(StrEnum):
    """Types of scheduling operations that can be triggered."""

    SCHEDULE = "schedule"  # Schedule pending sessions
    DEPRIORITIZE = "deprioritize"  # Lower priority and return to PENDING
    SWEEP = "sweep"  # Sweep stale sessions (maintenance operation)
    CHECK_PRECONDITION = "check_precondition"  # Check preconditions for scheduled sessions
    START = "start"  # Start prepared sessions
    TERMINATE = "terminate"  # Terminate sessions
    CHECK_PULLING_PROGRESS = "check_pulling_progress"  # Check if PULLING sessions can transition
    CHECK_CREATING_PROGRESS = (
        "check_creating_progress"  # Check if CREATING sessions can transition to RUNNING
    )
    CHECK_TERMINATING_PROGRESS = (
        "check_terminating_progress"  # Check if TERMINATING sessions can transition to TERMINATED
    )
    SWEEP_STALE_KERNELS = "sweep_stale_kernels"  # Sweep kernels with stale presence status
    DETECT_KERNEL_TERMINATION = (
        "detect_kernel_termination"  # Detect active sessions with any kernel TERMINATED/CANCELLED
    )
    OBSERVE_FAIR_SHARE = "observe_fair_share"  # Observe RUNNING kernels for fair share calculation
    CLEANUP_FORCE_TERMINATED = (
        "cleanup_force_terminated"  # Cleanup containers for force-terminated sessions
    )
