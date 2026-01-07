"""
Scheduler operation handlers.
"""

from .base import SchedulerHandler, SessionLifecycleHandler
from .lifecycle.schedule_sessions import (
    ScheduleSessionsHandler,
    ScheduleSessionsLifecycleHandler,
)
from .lifecycle.start_sessions import StartSessionsHandler, StartSessionsLifecycleHandler
from .lifecycle.terminate_sessions import (
    TerminateSessionsHandler,
    TerminateSessionsLifecycleHandler,
)
from .maintenance.sweep_lost_agent_kernels import (
    SweepLostAgentKernelsHandler,
    SweepLostAgentKernelsLifecycleHandler,
)
from .maintenance.sweep_sessions import SweepSessionsHandler, SweepSessionsLifecycleHandler
from .maintenance.sweep_stale_kernels import (
    SweepStaleKernelsHandler,
    SweepStaleKernelsLifecycleHandler,
)
from .progress.check_creating_progress import (
    CheckCreatingProgressHandler,
    CheckCreatingProgressLifecycleHandler,
)
from .progress.check_precondition import (
    CheckPreconditionHandler,
    CheckPreconditionLifecycleHandler,
)
from .progress.check_pulling_progress import (
    CheckPullingProgressHandler,
    CheckPullingProgressLifecycleHandler,
)
from .progress.check_running_session_termination import (
    CheckRunningSessionTerminationHandler,
    CheckRunningSessionTerminationLifecycleHandler,
)
from .progress.check_terminating_progress import (
    CheckTerminatingProgressHandler,
    CheckTerminatingProgressLifecycleHandler,
)
from .recovery.retry_creating import RetryCreatingHandler, RetryCreatingLifecycleHandler
from .recovery.retry_preparing import RetryPreparingHandler, RetryPreparingLifecycleHandler

__all__ = [
    # Legacy handlers (SchedulerHandler interface)
    "CheckCreatingProgressHandler",
    "CheckPreconditionHandler",
    "CheckPullingProgressHandler",
    "CheckRunningSessionTerminationHandler",
    "CheckTerminatingProgressHandler",
    "RetryCreatingHandler",
    "RetryPreparingHandler",
    "ScheduleSessionsHandler",
    "SchedulerHandler",
    "StartSessionsHandler",
    "SweepLostAgentKernelsHandler",
    "SweepSessionsHandler",
    "SweepStaleKernelsHandler",
    "TerminateSessionsHandler",
    # New lifecycle handlers (SessionLifecycleHandler interface)
    "SessionLifecycleHandler",
    "CheckCreatingProgressLifecycleHandler",
    "CheckPreconditionLifecycleHandler",
    "CheckPullingProgressLifecycleHandler",
    "CheckRunningSessionTerminationLifecycleHandler",
    "CheckTerminatingProgressLifecycleHandler",
    "RetryCreatingLifecycleHandler",
    "RetryPreparingLifecycleHandler",
    "ScheduleSessionsLifecycleHandler",
    "StartSessionsLifecycleHandler",
    "SweepLostAgentKernelsLifecycleHandler",
    "SweepSessionsLifecycleHandler",
    "SweepStaleKernelsLifecycleHandler",
    "TerminateSessionsLifecycleHandler",
]
