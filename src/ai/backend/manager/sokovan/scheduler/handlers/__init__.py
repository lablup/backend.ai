"""
Scheduler operation handlers.
"""

from .base import SessionLifecycleHandler
from .lifecycle.check_precondition import CheckPreconditionLifecycleHandler
from .lifecycle.schedule_sessions import ScheduleSessionsLifecycleHandler
from .lifecycle.start_sessions import StartSessionsLifecycleHandler
from .lifecycle.terminate_sessions import TerminateSessionsLifecycleHandler
from .maintenance.sweep_lost_agent_kernels import SweepLostAgentKernelsLifecycleHandler
from .maintenance.sweep_sessions import SweepSessionsLifecycleHandler
from .maintenance.sweep_stale_kernels import SweepStaleKernelsLifecycleHandler
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
    "CheckPreconditionLifecycleHandler",
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
