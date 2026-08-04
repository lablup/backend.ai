"""add confidential computing plane

Revision ID: c1f0a7d3b9e2
Revises: b4c5d6e7f8a9
Create Date: 2026-08-04

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pgsql

from ai.backend.manager.models.base import GUID

revision = "c1f0a7d3b9e2"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scaling_groups",
        sa.Column(
            "confidential",
            pgsql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_table(
        "confidential_reference_values",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("endpoint", sa.String(length=1024), nullable=False),
        sa.Column("image_digest", sa.String(length=256), nullable=False),
        sa.Column("profile_version", sa.String(length=64), nullable=False),
        sa.Column("measurements", pgsql.JSONB(), nullable=False),
        sa.Column("pipeline_signature", sa.Text, nullable=False),
        sa.Column("registered_by", sa.String(length=256), nullable=False),
        sa.Column("state", sa.String(length=64), nullable=False),
        sa.Column("supersedes", GUID, nullable=True),
        sa.Column("coexistence_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_confidential_refval_endpoint_state",
        "confidential_reference_values",
        ["endpoint", "state"],
    )
    op.create_table(
        "confidential_policy_journal",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("endpoint", sa.String(length=1024), nullable=False, index=True),
        sa.Column("content_hash", sa.String(length=71), nullable=False),
        sa.Column("document", sa.Text, nullable=False),
        sa.Column(
            "composed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("upload_failure", sa.Text, nullable=True),
    )
    op.create_table(
        "confidential_session_resources",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", GUID, nullable=False, index=True),
        sa.Column("endpoint", sa.String(length=1024), nullable=False),
        sa.Column("resource_path", sa.String(length=512), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("endpoint", "resource_path", name="uq_conf_resource_path"),
    )
    op.create_table(
        "confidential_nonces",
        sa.Column("session_id", GUID, primary_key=True),
        sa.Column("nonce", sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column("endpoint", sa.String(length=1024), nullable=False),
        sa.Column("domain_name", sa.String(length=64), nullable=False),
        sa.Column("image_digest", sa.String(length=256), nullable=False),
        sa.Column("profile_version", sa.String(length=64), nullable=False),
        sa.Column("quota", sa.Integer, nullable=False),
        sa.Column("claims_used", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "confidential_guest_claims",
        sa.Column("nonce", sa.String(length=128), primary_key=True),
        sa.Column("guest", sa.String(length=128), primary_key=True),
        sa.Column("session_id", GUID, nullable=False, index=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "confidential_decisions",
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
            index=True,
        ),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("verdict", sa.String(length=64), nullable=False, index=True),
        sa.Column("resource_path", sa.String(length=512), nullable=False),
        sa.Column("measurement", sa.Text, nullable=True),
        sa.Column("failing_clause", sa.Text, nullable=True),
        sa.Column("session_id", GUID, nullable=True),
        sa.Column("nonce", sa.String(length=128), nullable=True),
    )
    op.create_table(
        "confidential_measured_blobs",
        sa.Column("endpoint", sa.String(length=1024), primary_key=True),
        sa.Column("image_digest", sa.String(length=256), primary_key=True),
        sa.Column("profile_version", sa.String(length=64), primary_key=True),
        sa.Column("blob_digest", sa.String(length=71), nullable=False),
        sa.Column("blob", sa.LargeBinary, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "confidential_tcb_grace",
        sa.Column("endpoint", sa.String(length=1024), primary_key=True),
        sa.Column("platform_status", sa.String(length=64), nullable=False),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("disclosure", sa.Text, nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("confidential_tcb_grace")
    op.drop_table("confidential_measured_blobs")
    op.drop_table("confidential_decisions")
    op.drop_table("confidential_guest_claims")
    op.drop_table("confidential_nonces")
    op.drop_table("confidential_session_resources")
    op.drop_table("confidential_policy_journal")
    op.drop_index(
        "ix_confidential_refval_endpoint_state", table_name="confidential_reference_values"
    )
    op.drop_table("confidential_reference_values")
    op.drop_column("scaling_groups", "confidential")
