from typing import Any, Self, override

from ai.backend.common.events.payload import AnycastEventPayload
from ai.backend.common.events.types import AbstractAnycastEvent, EventDomain
from ai.backend.common.events.user_event.user_event import UserEvent


class ScheduleEventPayload(AnycastEventPayload):
    """A bare schedule trigger carries no arguments."""


class SokovanProcessEventPayload(AnycastEventPayload):
    schedule_type: str


class DeploymentLifecycleEventPayload(AnycastEventPayload):
    lifecycle_type: str
    sub_step: str | None = None


class RouteLifecycleEventPayload(AnycastEventPayload):
    lifecycle_type: str


class ReconcileProcessEventPayload(AnycastEventPayload):
    reconcile_type: str


class BaseScheduleEvent(AbstractAnycastEvent[ScheduleEventPayload]):
    @override
    def serialize(self) -> tuple[Any, ...]:
        return tuple()

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls()

    @override
    def to_payload(self) -> ScheduleEventPayload:
        return ScheduleEventPayload()

    @classmethod
    @override
    def from_payload(cls, payload: ScheduleEventPayload) -> Self:
        return cls()

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


class DoSokovanProcessIfNeededEvent(AbstractAnycastEvent[SokovanProcessEventPayload]):
    """Event to trigger Sokovan scheduler to process if marks are present (short cycle)."""

    schedule_type: str

    def __init__(self, schedule_type: str) -> None:
        self.schedule_type = schedule_type

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.schedule_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(schedule_type=value[0])

    @override
    def to_payload(self) -> SokovanProcessEventPayload:
        return SokovanProcessEventPayload(
            schedule_type=self.schedule_type,
        )

    @classmethod
    @override
    def from_payload(cls, payload: SokovanProcessEventPayload) -> Self:
        return cls(
            schedule_type=payload.schedule_type,
        )

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


class DoSokovanProcessScheduleEvent(AbstractAnycastEvent[SokovanProcessEventPayload]):
    """Event to trigger Sokovan scheduler to process unconditionally (long cycle)."""

    def __init__(self, schedule_type: str) -> None:
        self.schedule_type = schedule_type

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.schedule_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(schedule_type=value[0])

    @override
    def to_payload(self) -> SokovanProcessEventPayload:
        return SokovanProcessEventPayload(
            schedule_type=self.schedule_type,
        )

    @classmethod
    @override
    def from_payload(cls, payload: SokovanProcessEventPayload) -> Self:
        return cls(
            schedule_type=payload.schedule_type,
        )

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


class DoDeploymentLifecycleIfNeededEvent(AbstractAnycastEvent[DeploymentLifecycleEventPayload]):
    """Event to trigger deployment lifecycle processing if needed (short cycle)."""

    lifecycle_type: str
    sub_step: str | None

    def __init__(self, lifecycle_type: str, sub_step: str | None = None) -> None:
        self.lifecycle_type = lifecycle_type
        self.sub_step = sub_step

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.lifecycle_type, self.sub_step)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(lifecycle_type=value[0], sub_step=value[1] if len(value) > 1 else None)

    @override
    def to_payload(self) -> DeploymentLifecycleEventPayload:
        return DeploymentLifecycleEventPayload(
            lifecycle_type=self.lifecycle_type,
            sub_step=self.sub_step,
        )

    @classmethod
    @override
    def from_payload(cls, payload: DeploymentLifecycleEventPayload) -> Self:
        return cls(
            lifecycle_type=payload.lifecycle_type,
            sub_step=payload.sub_step,
        )

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


class DoDeploymentLifecycleEvent(AbstractAnycastEvent[DeploymentLifecycleEventPayload]):
    """Event to trigger deployment lifecycle processing unconditionally (long cycle)."""

    lifecycle_type: str
    sub_step: str | None

    def __init__(self, lifecycle_type: str, sub_step: str | None = None) -> None:
        self.lifecycle_type = lifecycle_type
        self.sub_step = sub_step

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.lifecycle_type, self.sub_step)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(lifecycle_type=value[0], sub_step=value[1] if len(value) > 1 else None)

    @override
    def to_payload(self) -> DeploymentLifecycleEventPayload:
        return DeploymentLifecycleEventPayload(
            lifecycle_type=self.lifecycle_type,
            sub_step=self.sub_step,
        )

    @classmethod
    @override
    def from_payload(cls, payload: DeploymentLifecycleEventPayload) -> Self:
        return cls(
            lifecycle_type=payload.lifecycle_type,
            sub_step=payload.sub_step,
        )

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


class DoRouteLifecycleIfNeededEvent(AbstractAnycastEvent[RouteLifecycleEventPayload]):
    """Event to trigger route lifecycle processing if needed (short cycle)."""

    lifecycle_type: str

    def __init__(self, lifecycle_type: str) -> None:
        self.lifecycle_type = lifecycle_type

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.lifecycle_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(lifecycle_type=value[0])

    @override
    def to_payload(self) -> RouteLifecycleEventPayload:
        return RouteLifecycleEventPayload(
            lifecycle_type=self.lifecycle_type,
        )

    @classmethod
    @override
    def from_payload(cls, payload: RouteLifecycleEventPayload) -> Self:
        return cls(
            lifecycle_type=payload.lifecycle_type,
        )

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


class DoRouteLifecycleEvent(AbstractAnycastEvent[RouteLifecycleEventPayload]):
    """Event to trigger route lifecycle processing unconditionally (long cycle)."""

    lifecycle_type: str

    def __init__(self, lifecycle_type: str) -> None:
        self.lifecycle_type = lifecycle_type

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.lifecycle_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(lifecycle_type=value[0])

    @override
    def to_payload(self) -> RouteLifecycleEventPayload:
        return RouteLifecycleEventPayload(
            lifecycle_type=self.lifecycle_type,
        )

    @classmethod
    @override
    def from_payload(cls, payload: RouteLifecycleEventPayload) -> Self:
        return cls(
            lifecycle_type=payload.lifecycle_type,
        )

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


class DoReconcileProcessIfNeededEvent(AbstractAnycastEvent[ReconcileProcessEventPayload]):
    """Event to trigger a generic reconcile stage if its needed-flag is set (short cycle)."""

    reconcile_type: str

    def __init__(self, reconcile_type: str) -> None:
        self.reconcile_type = reconcile_type

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.reconcile_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(reconcile_type=value[0])

    @override
    def to_payload(self) -> ReconcileProcessEventPayload:
        return ReconcileProcessEventPayload(
            reconcile_type=self.reconcile_type,
        )

    @classmethod
    @override
    def from_payload(cls, payload: ReconcileProcessEventPayload) -> Self:
        return cls(
            reconcile_type=payload.reconcile_type,
        )

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


class DoReconcileProcessEvent(AbstractAnycastEvent[ReconcileProcessEventPayload]):
    """Event to trigger a generic reconcile stage unconditionally (long cycle)."""

    reconcile_type: str

    def __init__(self, reconcile_type: str) -> None:
        self.reconcile_type = reconcile_type

    @override
    def serialize(self) -> tuple[Any, ...]:
        return (self.reconcile_type,)

    @classmethod
    @override
    def deserialize(cls, value: tuple[Any, ...]) -> Self:
        return cls(reconcile_type=value[0])

    @override
    def to_payload(self) -> ReconcileProcessEventPayload:
        return ReconcileProcessEventPayload(
            reconcile_type=self.reconcile_type,
        )

    @classmethod
    @override
    def from_payload(cls, payload: ReconcileProcessEventPayload) -> Self:
        return cls(
            reconcile_type=payload.reconcile_type,
        )

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
