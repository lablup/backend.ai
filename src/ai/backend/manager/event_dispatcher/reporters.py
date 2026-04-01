from ai.backend.common.events.reporter import (
    AbstractEventReporter,
    CompleteEventReportArgs,
    PrepareEventReportArgs,
)
from ai.backend.common.events.types import AbstractEvent
from ai.backend.manager.models.event_log import EventLogRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class EventLogger(AbstractEventReporter):
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def prepare_event_report(
        self,
        event: AbstractEvent,
        arg: PrepareEventReportArgs,
    ) -> None:
        async with self._db.begin_session() as session:
            event_log = EventLogRow.from_event(event)
            session.add(event_log)
            await session.flush()

    async def complete_event_report(
        self,
        event: AbstractEvent,
        arg: CompleteEventReportArgs,
    ) -> None:
        return
