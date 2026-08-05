from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.models.base import (
    GUID,
    Base,
)
from ai.backend.manager.models.mixins.timestamp import CreatedAtMixin


class EntityFieldRow(CreatedAtMixin, Base):  # type: ignore[misc]
    """Deprecated: No longer actively used. The field-scoped entity concept
    (RBACFieldCreator/RBACFieldPurger) was removed by BEP-1048.
    Kept only for the existing database table; will be dropped in a future migration.
    """

    __tablename__ = "entity_fields"
    __table_args__ = (
        sa.UniqueConstraint(
            "entity_type",
            "entity_id",
            "field_type",
            "field_id",
            name="uq_entity_fields_mapping",
        ),
        sa.Index("ix_entity_fields_entity_lookup", "entity_type", "entity_id"),
        sa.Index("ix_entity_fields_field_lookup", "field_type", "field_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        "id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )

    entity_type: Mapped[str] = mapped_column(
        "entity_type",
        sa.String(64),
        nullable=False,
    )
    entity_id: Mapped[str] = mapped_column(
        "entity_id",
        sa.String(64),
        nullable=False,
    )
    field_type: Mapped[str] = mapped_column(
        "field_type",
        sa.String(64),
        nullable=False,
    )
    field_id: Mapped[str] = mapped_column(
        "field_id",
        sa.String(64),
        nullable=False,
    )
