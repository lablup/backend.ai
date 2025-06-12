from abc import ABC, abstractmethod
from dataclasses import dataclass

from .types import AbstractEvent


@dataclass
class PrepareEventReportArgs:
    pass


@dataclass
class CompleteEventReportArgs:
    duration: float


class AbstractEventReporter(ABC):
    @abstractmethod
    async def prepare_event_report(
        self,
        event: AbstractEvent,
        arg: PrepareEventReportArgs,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def complete_event_report(
        self,
        event: AbstractEvent,
        arg: CompleteEventReportArgs,
    ) -> None:
        raise NotImplementedError
