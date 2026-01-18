"""
Scheduler operation handlers.
"""

from .base import SessionLifecycleHandler
from .lifecycle.schedule_sessions import ScheduleSessionsLifecycleHandler
from .lifecycle.start_sessions import StartSessionsLifecycleHandler
from .lifecycle.terminate_sessions import TerminateSessionsLifecycleHandler
from .maintenance.sweep_lost_agent_kernels import SweepLostAgentKernelsLifecycleHandler
from .maintenance.sweep_sessions import SweepSessionsLifecycleHandler
from .maintenance.sweep_stale_kernels import SweepStaleKernelsLifecycleHandler
from .progress.check_creating_progress import CheckCreatingProgressLifecycleHandler
from .progress.check_precondition import CheckPreconditionLifecycleHandler
from .progress.check_pulling_progress import CheckPullingProgressLifecycleHandler
from .progress.check_running_session_termination import (
    CheckRunningSessionTerminationLifecycleHandler,
)
from .progress.check_terminating_progress import CheckTerminatingProgressLifecycleHandler
from .promotion.base import SessionPromotionHandler
from .promotion.detect_termination import DetectTerminationPromotionHandler
from .promotion.promote_to_prepared import PromoteToPreparedPromotionHandler
from .promotion.promote_to_running import PromoteToRunningPromotionHandler
from .promotion.promote_to_terminated import PromoteToTerminatedPromotionHandler
from .recovery.retry_creating import RetryCreatingLifecycleHandler
from .recovery.retry_preparing import RetryPreparingLifecycleHandler

__all__ = [
    # Session lifecycle handlers (SessionLifecycleHandler interface)
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
    # Session promotion handlers (SessionPromotionHandler interface)
    "SessionPromotionHandler",
    "DetectTerminationPromotionHandler",
    "PromoteToPreparedPromotionHandler",
    "PromoteToRunningPromotionHandler",
    "PromoteToTerminatedPromotionHandler",
]
