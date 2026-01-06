from __future__ import annotations

import sqlalchemy as sa

from ai.backend.manager.models.base import (
    Base,
    IDColumn,
)


class EntityFieldRow(Base):
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

    id = IDColumn()

    entity_type = sa.Column(
        "entity_type",
        sa.String(64),
        nullable=False,
    )
    entity_id = sa.Column(
        "entity_id",
        sa.String(64),
        nullable=False,
    )
    field_type = sa.Column(
        "field_type",
        sa.String(64),
        nullable=False,
    )
    field_id = sa.Column(
        "field_id",
        sa.String(64),
        nullable=False,
    )
    created_at = sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
        server_default=sa.func.now(),
    )
