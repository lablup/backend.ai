from typing import Self

import sqlalchemy as sa

from ai.backend.common.events.types import AbstractEvent, EventDomain

from .base import (
    Base,
    IDColumn,
    StrEnumType,
)

__all__ = ("EventLogRow",)


class EventLogRow(Base):
    __tablename__ = "event_logs"

    id = IDColumn("id")

    event_name = sa.Column("event_name", sa.String, nullable=False)
    event_domain = sa.Column(
        "event_domain",
        StrEnumType(EventDomain),
        nullable=False,
    )
    domain_id = sa.Column("domain_id", sa.String, nullable=True, index=True)

    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )
    duration = sa.Column("duration", sa.Interval, nullable=True)

    @classmethod
    def from_event(cls, event: AbstractEvent) -> Self:
        event_name = event.event_name()
        event_domain = event.event_domain()
        event_domain_id = event.domain_id()
        return EventLogRow(
            event_name=event_name,
            event_domain=event_domain,
            domain_id=event_domain_id,
        )
