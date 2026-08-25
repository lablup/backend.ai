from typing import override

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class BaseScheduleEvent(AbstractAnycastEvent):
    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoSokovanProcessIfNeededEvent(AbstractAnycastEvent):
    """Event to trigger Sokovan scheduler to process if marks are present (short cycle)."""

    schedule_type: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_sokovan_process_if_needed"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoSokovanProcessScheduleEvent(AbstractAnycastEvent):
    """Event to trigger Sokovan scheduler to process unconditionally (long cycle)."""

    schedule_type: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_sokovan_process_schedule"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoDeploymentLifecycleIfNeededEvent(AbstractAnycastEvent):
    """Event to trigger deployment lifecycle processing if needed (short cycle)."""

    lifecycle_type: str
    sub_step: str | None = None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_deployment_lifecycle_if_needed"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoDeploymentLifecycleEvent(AbstractAnycastEvent):
    """Event to trigger deployment lifecycle processing unconditionally (long cycle)."""

    lifecycle_type: str
    sub_step: str | None = None

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_deployment_lifecycle"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoRouteLifecycleIfNeededEvent(AbstractAnycastEvent):
    """Event to trigger route lifecycle processing if needed (short cycle)."""

    lifecycle_type: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_route_lifecycle_if_needed"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoRouteLifecycleEvent(AbstractAnycastEvent):
    """Event to trigger route lifecycle processing unconditionally (long cycle)."""

    lifecycle_type: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_route_lifecycle"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoReconcileProcessIfNeededEvent(AbstractAnycastEvent):
    """Event to trigger a generic reconcile stage if its needed-flag is set (short cycle)."""

    reconcile_type: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_reconcile_process_if_needed"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None


class DoReconcileProcessEvent(AbstractAnycastEvent):
    """Event to trigger a generic reconcile stage unconditionally (long cycle)."""

    reconcile_type: str

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_reconcile_process"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> str | None:
        return None

    @override
    def user_event(self) -> UserEvent | None:
        return None
