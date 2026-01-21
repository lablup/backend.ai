"""Update AuditLog table

Revision ID: 305e3ddc20a7
Revises: c4ea15b77136
Create Date: 2025-04-11 12:16:49.931839

"""

import logging
import uuid
from datetime import timedelta
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import registry

from ai.backend.manager.models.base import GUID, convention

# revision identifiers, used by Alembic.
revision = "305e3ddc20a7"
down_revision = "c4ea15b77136"
branch_labels = None
depends_on = None

logger = logging.getLogger("alembic.runtime.migration")


NULL_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")

metadata = sa.MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)
Base: Any = mapper_registry.generate_base()


class AuditLogRowInUpgrade(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    id = sa.Column("id", GUID, primary_key=True)
    entity_type = sa.Column("entity_type", sa.String, nullable=False)
    operation = sa.Column("operation", sa.String, nullable=False)
    entity_id = sa.Column("entity_id", sa.String, nullable=False)
    created_at = sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)
    request_id = sa.Column("request_id", GUID, nullable=False)
    description = sa.Column("description", sa.String, nullable=False)
    duration = sa.Column("duration", sa.Interval, nullable=False)
    status = sa.Column("status", sa.String(length=64), nullable=False)


class AuditLogRowInDowngrade(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}

    id = sa.Column("id", GUID, primary_key=True)
    entity_type = sa.Column("entity_type", sa.String, nullable=False)
    operation = sa.Column("operation", sa.String, nullable=False)
    entity_id = sa.Column("entity_id", sa.String, nullable=False)
    created_at = sa.Column("created_at", sa.DateTime(timezone=True), nullable=False)
    request_id = sa.Column("request_id", GUID, nullable=False)
    description = sa.Column("description", sa.String, nullable=False)
    duration = sa.Column("duration", sa.Interval, nullable=True)
    status = sa.Column("status", sa.String(length=64), nullable=False)
    action_id = sa.Column("action_id", GUID, nullable=False)


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("action_id", GUID, nullable=True))

    try:
        op.execute(
            sa.update(AuditLogRowInUpgrade).values(
                action_id=NULL_UUID,
            )
        )
    except Exception as e:
        logger.error(f"Error updating audit_logs.action_id: {e}")
        raise

    op.alter_column("audit_logs", "action_id", nullable=False)
    op.alter_column("audit_logs", "duration", nullable=True)


def downgrade() -> None:
    try:
        op.execute(
            sa.update(AuditLogRowInDowngrade)
            .where(AuditLogRowInDowngrade.duration.is_(None))
            .values(duration=timedelta(0))
        )
    except Exception as e:
        logger.error(f"Error updating audit_logs.duration: {e}")
        raise

    op.alter_column("audit_logs", "duration", nullable=False)
    op.drop_column("audit_logs", "action_id")
