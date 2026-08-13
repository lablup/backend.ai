"""Shared mixins for record audit timestamps.

Mirrors ``manager/models/mixins/timestamp.py``. The two components cannot share
one module because ``ai.backend.common`` carries no SQLAlchemy dependency.
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        sort_order=9998,
    )


class UpdatedAtMixin:
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        sort_order=9999,
    )


class LifecycleTimestampsMixin(CreatedAtMixin, UpdatedAtMixin):
    pass
