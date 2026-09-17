from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.global_entity import GlobalEntityID, GlobalEntityName
from ai.backend.manager.models.base import GUID, Base, StrEnumType
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = ("GlobalEntityRow",)


class GlobalEntityRow(CreatedAtMixin, Base):
    """A singleton scope. Rows are written by the migration."""

    __tablename__ = "global_entities"

    id: Mapped[GlobalEntityID] = mapped_column(
        "id",
        GUID(GlobalEntityID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v7()"),
    )
    name: Mapped[GlobalEntityName] = mapped_column(
        "name", StrEnumType(GlobalEntityName, length=32), nullable=False, unique=True
    )
