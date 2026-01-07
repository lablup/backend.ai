"""
Scheduler operation handlers.
"""

from .base import SchedulerHandler, SessionLifecycleHandler
from .lifecycle.schedule_sessions import ScheduleSessionsHandler
from .lifecycle.start_sessions import StartSessionsHandler
from .lifecycle.terminate_sessions import TerminateSessionsHandler
from .maintenance.sweep_lost_agent_kernels import SweepLostAgentKernelsHandler
from .maintenance.sweep_sessions import SweepSessionsHandler
from .maintenance.sweep_stale_kernels import SweepStaleKernelsHandler
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
from .recovery.retry_creating import RetryCreatingHandler
from .recovery.retry_preparing import RetryPreparingHandler

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
]
