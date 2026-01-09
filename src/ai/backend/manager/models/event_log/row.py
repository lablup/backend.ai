from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Self

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.events.types import AbstractEvent, EventDomain
from ai.backend.manager.models.base import (
    GUID,
    Base,
    StrEnumType,
)

__all__ = ("EventLogRow",)


class EventLogRow(Base):
    __tablename__ = "event_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    event_name: Mapped[str] = mapped_column("event_name", sa.String, nullable=False)
    event_domain: Mapped[EventDomain] = mapped_column(
        "event_domain",
        StrEnumType(EventDomain),
        nullable=False,
    )
    domain_id: Mapped[str | None] = mapped_column("domain_id", sa.String, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )
    duration: Mapped[timedelta | None] = mapped_column("duration", sa.Interval, nullable=True)

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
