"""Update AuditLog table

Revision ID: 305e3ddc20a7
Revises: c4ea15b77136
Create Date: 2025-04-11 12:16:49.931839

"""

import logging
import uuid

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
Base = mapper_registry.generate_base()


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
    started_at = sa.Column("started_at", sa.DateTime(timezone=True), nullable=False)
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
    op.add_column("audit_logs", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))

    try:
        op.execute(
            sa.update(AuditLogRowInUpgrade).values(
                started_at=AuditLogRowInUpgrade.created_at,
            )
        )
    except Exception as e:
        logger.error(f"Error updating audit_logs.started_at: {e}")
        raise

    op.alter_column("audit_logs", "started_at", nullable=False)
    op.create_index(op.f("ix_audit_logs_started_at"), "audit_logs", ["started_at"], unique=False)
    op.drop_index(op.f("ix_audit_logs_created_at"), table_name="audit_logs")
    op.drop_column("audit_logs", "created_at")


def downgrade() -> None:
    op.add_column("audit_logs", sa.Column("created_at", sa.DateTime(timezone=True), nullable=True))

    try:
        op.execute(
            sa.update(AuditLogRowInDowngrade).values(
                created_at=AuditLogRowInDowngrade.started_at,
            )
        )
    except Exception as e:
        logger.error(f"Error updating audit_logs.created_at: {e}")
        raise

    op.alter_column("audit_logs", "created_at", nullable=False)
    op.create_index(op.f("ix_audit_logs_created_at"), "audit_logs", ["created_at"], unique=False)
    op.drop_index(op.f("ix_audit_logs_started_at"), table_name="audit_logs")
    op.drop_column("audit_logs", "started_at")
    op.drop_column("audit_logs", "action_id")
