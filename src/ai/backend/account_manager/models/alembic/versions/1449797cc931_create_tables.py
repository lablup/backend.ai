"""create tables

Revision ID: 1449797cc931
Revises:
Create Date: 2024-08-09 23:48:43.204523

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

from ai.backend.account_manager.models.base import GUID, PasswordColumn

# revision identifiers, used by Alembic.
revision: str = "1449797cc931"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
    op.create_table(
        "applications",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("redirect_to", sa.Text(), nullable=True),
        sa.Column("token_secret", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_applications")),
        sa.UniqueConstraint("name", name=op.f("uq_applications_name")),
    )
    op.create_table(
        "association_applications_users",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("application_id", GUID(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_association_applications_users")),
        sa.Index("ix_user_id_application_id", "user_id", "application_id", unique=True),
    )
    op.create_table(
        "keypairs",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", GUID(), nullable=True),
        sa.Column("access_key", sa.String(length=20), nullable=True),
        sa.Column("secret_key", sa.String(length=40), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_keypairs")),
        sa.UniqueConstraint("access_key", name=op.f("uq_keypairs_access_key")),
    )
    op.create_index(op.f("ix_keypairs_is_active"), "keypairs", ["is_active"], unique=False)
    op.create_table(
        "user_profiles",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=64), nullable=False),
        sa.Column("password", PasswordColumn(), nullable=False),
        sa.Column("need_password_change", sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column(
            "password_changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column("full_name", sa.String(length=64), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("role", sa.VARCHAR(length=64), server_default="user", nullable=False),
        sa.Column("status", sa.VARCHAR(length=64), server_default="active", nullable=False),
        sa.Column("status_info", sa.Unicode(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_profiles")),
    )
    op.create_index(op.f("ix_user_profiles_email"), "user_profiles", ["email"], unique=False)
    op.create_index(op.f("ix_user_profiles_username"), "user_profiles", ["username"], unique=True)
    op.create_table(
        "users",
        sa.Column("uuid", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_users")),
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_index(op.f("ix_user_profiles_username"), table_name="user_profiles")
    op.drop_index(op.f("ix_user_profiles_email"), table_name="user_profiles")
    op.drop_table("user_profiles")
    op.drop_index(op.f("ix_keypairs_is_active"), table_name="keypairs")
    op.drop_table("keypairs")
    op.drop_index(op.f("ix_user_id_application_id"), table_name="association_applications_users")
    op.drop_table("association_applications_users")
    op.drop_table("applications")
