from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.common.data.entity.virtual_entity import VirtualEntityID
from ai.backend.common.data.permission.virtual_entity import VirtualEntityData
from ai.backend.manager.models.base import (
    GUID,
    Base,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class VirtualEntityRow(CreatedAtMixin, Base):
    """Graph-side counterpart of a real entity row kept in its own domain table.
    Reference anchor for the entity and parent of its membership edges."""

    __tablename__ = "virtual_entities"
    __table_args__ = (
        sa.UniqueConstraint("entity_type", "entity_id", name="uq_virtual_entities_entity"),
    )

    id: Mapped[VirtualEntityID] = mapped_column(
        "id",
        GUID(VirtualEntityID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", sa.String(length=32), nullable=False
    )
    entity_id: Mapped[EntityID] = mapped_column("entity_id", GUID(), nullable=False)

    def to_data(self) -> VirtualEntityData:
        return VirtualEntityData(
            id=self.id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
        )
