from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.entity_label import EntityLabelID, EntityLabelKey
from ai.backend.common.data.entity.types import EntityID, EntityType, RuntimeEntityID
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import LifecycleTimestampsMixin

__all__ = ("EntityLabelRow",)


class EntityLabelRow(LifecycleTimestampsMixin, Base):
    """One ``key=value`` label on one entity.

    The entity is a polymorphic ``(entity_type, entity_id)`` pair with no foreign key, so
    a label goes on any type without the schema knowing it. A label is an attribute of
    the entity, not a graph edge, which is why it does not name the entity's virtual
    entity node.
    One value per key: putting a key on an entity that already carries it replaces the
    value.
    """

    __tablename__ = "entity_labels"
    __table_args__ = (
        sa.UniqueConstraint("entity_type", "entity_id", "key", name="uq_entity_labels_key"),
        sa.Index("ix_entity_labels_entity", "entity_type", "entity_id"),
        sa.Index("ix_entity_labels_pair", "key", "value"),
    )

    id: Mapped[EntityLabelID] = mapped_column(
        "id",
        GUID(EntityLabelID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", sa.String(length=32), nullable=False
    )
    entity_id: Mapped[EntityID] = mapped_column("entity_id", GUID(), nullable=False)
    key: Mapped[EntityLabelKey] = mapped_column("key", sa.String(length=255), nullable=False)
    value: Mapped[str] = mapped_column("value", sa.String(length=255), nullable=False)

    def to_data(self) -> EntityLabelData:
        return EntityLabelData(
            id=self.id,
            entity=RuntimeEntityID(self.entity_type, self.entity_id),
            key=self.key,
            value=self.value,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
