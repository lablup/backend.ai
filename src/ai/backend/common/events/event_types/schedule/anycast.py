from typing import Optional, Self, override

from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class BaseScheduleEvent(AbstractAnycastEvent):
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
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoScheduleEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_schedule"


class DoCheckPrecondEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_check_precond"


class DoStartSessionEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_start_session"


class DoScaleEvent(BaseScheduleEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_scale"


class DoSokovanProcessIfNeededEvent(AbstractAnycastEvent):
    """Event to trigger Sokovan scheduler to process if marks are present (short cycle)."""

    schedule_type: str

    def __init__(self, schedule_type: str) -> None:
        self.schedule_type = schedule_type

    @override
    def serialize(self) -> tuple:
        return (self.schedule_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(schedule_type=value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_sokovan_process_if_needed"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoSokovanProcessScheduleEvent(AbstractAnycastEvent):
    """Event to trigger Sokovan scheduler to process unconditionally (long cycle)."""

    def __init__(self, schedule_type: str) -> None:
        self.schedule_type = schedule_type

    @override
    def serialize(self) -> tuple:
        return (self.schedule_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(schedule_type=value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_sokovan_process_schedule"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoDeploymentLifecycleIfNeededEvent(AbstractAnycastEvent):
    """Event to trigger deployment lifecycle processing if needed (short cycle)."""

    lifecycle_type: str

    def __init__(self, lifecycle_type: str) -> None:
        self.lifecycle_type = lifecycle_type

    @override
    def serialize(self) -> tuple:
        return (self.lifecycle_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(lifecycle_type=value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_deployment_lifecycle_if_needed"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoDeploymentLifecycleEvent(AbstractAnycastEvent):
    """Event to trigger deployment lifecycle processing unconditionally (long cycle)."""

    lifecycle_type: str

    def __init__(self, lifecycle_type: str) -> None:
        self.lifecycle_type = lifecycle_type

    @override
    def serialize(self) -> tuple:
        return (self.lifecycle_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(lifecycle_type=value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_deployment_lifecycle"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoRouteLifecycleIfNeededEvent(AbstractAnycastEvent):
    """Event to trigger route lifecycle processing if needed (short cycle)."""

    lifecycle_type: str

    def __init__(self, lifecycle_type: str) -> None:
        self.lifecycle_type = lifecycle_type

    @override
    def serialize(self) -> tuple:
        return (self.lifecycle_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(lifecycle_type=value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_route_lifecycle_if_needed"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None


class DoRouteLifecycleEvent(AbstractAnycastEvent):
    """Event to trigger route lifecycle processing unconditionally (long cycle)."""

    lifecycle_type: str

    def __init__(self, lifecycle_type: str) -> None:
        self.lifecycle_type = lifecycle_type

    @override
    def serialize(self) -> tuple:
        return (self.lifecycle_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple) -> Self:
        return cls(lifecycle_type=value[0])

    @classmethod
    @override
    def event_name(cls) -> str:
        return "do_route_lifecycle"

    @classmethod
    @override
    def event_domain(cls) -> EventDomain:
        return EventDomain.SCHEDULE

    @override
    def domain_id(self) -> Optional[str]:
        return None

    @override
    def user_event(self) -> Optional[UserEvent]:
        return None
