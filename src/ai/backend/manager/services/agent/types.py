import enum


class ConflictingSessionCleanupPolicy(enum.StrEnum):
    """
    How to clean up sessions that conflict with an agent's resource group.

    A session conflicts when its kernels were scheduled on the agent under a
    resource group that no longer matches the agent's current (authoritative)
    resource group.
    """

    TERMINATE = "terminate"
    # Re-enqueue conflicting sessions back to PENDING. Not yet implemented: it
    # depends on the RESCHEDULING state introduced by the preemption work.
    RESCHEDULE = "reschedule"
