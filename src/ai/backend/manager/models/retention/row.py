from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.retention.types import RetentionCategory
from ai.backend.manager.models.base import GUID, Base, StrEnumType


class RetentionPolicyRow(Base):  # type: ignore[misc]
    __tablename__ = "retention_policies"
    __table_args__ = (sa.UniqueConstraint("category", name="uq_retention_policies_category"),)

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    category: Mapped[RetentionCategory] = mapped_column(
        "category", StrEnumType(RetentionCategory), nullable=False
    )
    retention_period: Mapped[timedelta] = mapped_column(
        "retention_period", sa.Interval, nullable=False
    )
    enabled: Mapped[bool] = mapped_column(
        "enabled", sa.Boolean, nullable=False, server_default=sa.true()
    )
    last_swept_at: Mapped[datetime | None] = mapped_column(
        "last_swept_at", sa.DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
    )
