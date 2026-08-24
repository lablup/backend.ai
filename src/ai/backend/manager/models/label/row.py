from __future__ import annotations

from typing import override

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.entity.label import LabelID, LabelKey
from ai.backend.common.data.entity.types import EntityID, EntityType
from ai.backend.manager.data.label.types import LabelData
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin

__all__ = ("LabelRow",)


class LabelRow(CreatedAtMixin, Base):
    """One ``key=value`` label on one entity.

    The entity is a polymorphic ``(entity_type, entity_id)`` pair with no foreign key, as
    the RBAC graph rows are, so a label goes on any type without the schema knowing it.
    """

    __tablename__ = "labels"
    __table_args__ = (
        sa.UniqueConstraint("entity_type", "entity_id", "key", "value", name="uq_labels_label"),
        sa.Index("ix_labels_entity", "entity_type", "entity_id"),
        sa.Index("ix_labels_pair", "key", "value"),
    )

    id: Mapped[LabelID] = mapped_column(
        "id",
        GUID(LabelID),
        primary_key=True,
        server_default=sa.text("uuid_generate_v4()"),
    )
    entity_type: Mapped[EntityType] = mapped_column(
        "entity_type", sa.String(length=32), nullable=False
    )
    entity_id: Mapped[EntityID] = mapped_column("entity_id", GUID(), nullable=False)
    key: Mapped[LabelKey] = mapped_column("key", sa.String(length=255), nullable=False)
    value: Mapped[str] = mapped_column("value", sa.String(length=255), nullable=False)

    def to_data(self) -> LabelData:
        return LabelData(
            id=self.id,
            entity_type=self.entity_type,
            entity_id=self.entity_id,
            key=self.key,
            value=self.value,
            created_at=self.created_at,
        )

    @override
    def __str__(self) -> str:
        return (
            f"LabelRow("
            f"id: {self.id}, "
            f"entity_type: {self.entity_type}, "
            f"entity_id: {self.entity_id}, "
            f"key: {self.key}, "
            f"value: {self.value}"
            f")"
        )

    @override
    def __repr__(self) -> str:
        return self.__str__()
