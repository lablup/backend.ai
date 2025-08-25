"""Auto-scaler for deployment management with global timer integration."""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Self, override

from ai.backend.common.distributed import GlobalTimer
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent
from ai.backend.logging.utils import BraceStyleAdapter
from ai.backend.manager.defs import LockID

if TYPE_CHECKING:
    from ai.backend.manager.types import DistributedLockFactory

    from .deployment_controller import DeploymentController

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class DeploymentAutoScaleEvent(AbstractAnycastEvent):
    """Event for triggering deployment auto-scaling."""

    @override
    def serialize(self) -> tuple:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls()

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.MODEL_SERVING

    @classmethod
    @override
    def event_name(cls) -> str:
        return "deployment_auto_scale"

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


@dataclass
class AutoScalerConfig:
    """Configuration for auto-scaler."""

    check_interval: float = 30.0  # Check every 30 seconds
    initial_delay: float = 60.0  # Wait 1 minute before first check
    lock_timeout: float = 45.0  # Lock timeout slightly longer than interval


class DeploymentAutoScaler:
    """
    Auto-scaler for deployment management.

    This class runs on a global timer to periodically:
    - Check deployment health
    - Scale services based on metrics
    - Recover failed routes
    """

    _deployment_controller: "DeploymentController"
    _event_producer: EventProducer
    _lock_factory: "DistributedLockFactory"
    _config: AutoScalerConfig
    _timer: GlobalTimer

    def __init__(
        self,
        deployment_controller: "DeploymentController",
        event_producer: EventProducer,
        lock_factory: "DistributedLockFactory",
        config: Optional[AutoScalerConfig] = None,
    ) -> None:
        self._deployment_controller = deployment_controller
        self._event_producer = event_producer
        self._lock_factory = lock_factory
        self._config = config or AutoScalerConfig()

    async def init_timer(self) -> None:
        """Initialize the global timer for auto-scaling operations."""
        # Create timer for auto-scaling operations
        # Following the pattern from sokovan.py
        self._timer = GlobalTimer(
            self._lock_factory(
                LockID.LOCKID_DEPLOYMENT_AUTO_SCALER,  # Need to add this to LockID enum
                self._config.lock_timeout,
            ),
            self._event_producer,
            lambda: DeploymentAutoScaleEvent(),  # Create event for auto-scaling
            interval=self._config.check_interval,
            initial_delay=self._config.initial_delay,
            task_name="deployment_auto_scaler",
        )

        await self._timer.join()
        log.info(
            "Deployment auto-scaler timer initialized (interval: {}s)",
            self._config.check_interval,
        )

    async def shutdown_timer(self) -> None:
        """Shutdown the auto-scaler timer gracefully."""
        if hasattr(self, "_timer"):
            await self._timer.leave()
            log.info("Deployment auto-scaler timer stopped")
