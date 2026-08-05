"""Shared mixins for record audit timestamps.

``CreatedAtMixin`` / ``UpdatedAtMixin`` each provide a single column so a table
can adopt exactly the ones it needs; ``LifecycleTimestampsMixin`` composes both
for the common create-and-update case. ``sort_order`` keeps the timestamps last
and ordered created -> updated regardless of the MRO.
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
