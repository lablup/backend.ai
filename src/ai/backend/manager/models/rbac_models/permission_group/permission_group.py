from __future__ import annotations

import uuid

import sqlalchemy as sa

from ...base import (
    GUID,
    Base,
    IDColumn,
)


class PermissionGroupRow(Base):
    __tablename__ = "permission_groups"
    __table_args__ = (sa.Index("ix_id_role_id", "id", "role_id"),)

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "permission_groups",
    }

    id: uuid.UUID = IDColumn()
    role_id: uuid.UUID = sa.Column("role_id", GUID, nullable=False)
    type: str = sa.Column("type", sa.String(32), nullable=False)
