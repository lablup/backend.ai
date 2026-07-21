from __future__ import annotations

from datetime import datetime, timedelta

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.identifier.retention_policy import RetentionPolicyID
from ai.backend.manager.data.retention.types import RetentionCategory, RetentionPolicyData
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin


class RetentionPolicyRow(LifecycleTimestampsMixin, Base):  # type: ignore[misc]
    __tablename__ = "retention_policies"
    __table_args__ = (sa.UniqueConstraint("category", name="uq_retention_policies_category"),)

    id: Mapped[RetentionPolicyID] = mapped_column(
        "id",
        GUID(RetentionPolicyID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    category: Mapped[RetentionCategory] = mapped_column(
        "category", StrEnumType(RetentionCategory), nullable=False
    )
    retention_period: Mapped[timedelta] = mapped_column(
        "retention_period", sa.Interval, nullable=False
    )
    enabled: Mapped[bool] = mapped_column(
        "enabled", sa.Boolean, nullable=False, server_default=sa.false()
    )
    last_swept_at: Mapped[datetime | None] = mapped_column(
        "last_swept_at", sa.DateTime(timezone=True), nullable=True
    )

    def to_data(self) -> RetentionPolicyData:
        return RetentionPolicyData(
            id=self.id,
            category=self.category,
            retention_period=self.retention_period,
            enabled=self.enabled,
            last_swept_at=self.last_swept_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
