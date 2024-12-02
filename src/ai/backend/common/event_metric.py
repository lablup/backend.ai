from typing import Protocol


class EventMetricProtocol(Protocol):
    def update_success_event_metric(self, *, event_type: str, duration: float) -> None: ...

    def update_failure_event_metric(self, *, event_type: str, duration: float) -> None: ...


class NopEventMetric:
    def update_success_event_metric(self, *, event_type: str, duration: float) -> None:
        pass

    def update_failure_event_metric(self, *, event_type: str, duration: float) -> None:
        pass
