import enum


class SubscribableEvents(enum.StrEnum):
    KERNEL_CANCELLED = "kernel_cancelled"
    KERNEL_CREATING = "kernel_creating"
    KERNEL_STARTED = "kernel_started"
    KERNEL_TERMINATED = "kernel_terminated"
    KERNEL_TERMINATING = "kernel_terminating"
    SESSION_FAILURE = "session_failure"
    SESSION_STARTED = "session_started"
    SESSION_SUCCESS = "session_success"
    SESSION_TERMINATED = "session_terminated"

    # Virtual event representing either success or failure for batch sessions
    BATCH_SESSION_RESULT = "batch_session_result"
