"""Shared mixin for soft-deletable rows.

``deleted_at`` alone says whether a row is soft-deleted; NULL means alive. It is written
only by the updaters in ``models/specs/soft_delete.py``.
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column


class SoftDeleteMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        "deleted_at",
        sa.DateTime(timezone=True),
        nullable=True,
        server_default=sa.null(),
        sort_order=10000,
    )
