"""replace_kernelrole_to_sessiontypes

Revision ID: 3596bc12ec09
Revises: c4b7ec740b36
Create Date: 2023-10-04 16:43:46.281383

"""

import enum
import uuid
from typing import cast

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

from ai.backend.manager.models.base import GUID, mapper_registry

# revision identifiers, used by Alembic.
revision = "3596bc12ec09"
down_revision = "c4b7ec740b36"
branch_labels = None
depends_on = None

ENUM_CLS = "sessiontypes"

PAGE_SIZE = 100


class KernelRole(enum.Enum):
    INFERENCE = "INFERENCE"
    COMPUTE = "COMPUTE"
    SYSTEM = "SYSTEM"


kernelrole_choices = list(map(lambda v: v.name, KernelRole))
kernelrole = postgresql.ENUM(*kernelrole_choices, name="kernelrole")


class OldSessionTypes(enum.StrEnum):
    INTERACTIVE = "interactive"
    BATCH = "batch"
    INFERENCE = "inference"


def upgrade():
    connection = op.get_bind()

    # Relax the sessions.session_type from enum to varchar(64).
    connection.execute(
        text(
            "ALTER TABLE sessions ALTER COLUMN session_type TYPE varchar(64) USING session_type::text;"
        )
    )
    connection.execute(
        text("ALTER TABLE sessions ALTER COLUMN session_type SET DEFAULT 'INTERACTIVE';")
    )

    # Relax the kernels.session_type from enum to varchar(64).
    connection.execute(
        text(
            "ALTER TABLE kernels ALTER COLUMN session_type TYPE varchar(64) USING session_type::text;"
        )
    )
    connection.execute(
        text("ALTER TABLE kernels ALTER COLUMN session_type SET DEFAULT 'INTERACTIVE';")
    )
    # Relax the kernels.role from enum to varchar(64).
    connection.execute(
        text("ALTER TABLE kernels ALTER COLUMN role TYPE varchar(64) USING role::text;")
    )
    connection.execute(text("ALTER TABLE kernels ALTER COLUMN role SET DEFAULT 'COMPUTE';"))

    # Drop enum types
    connection.execute(text("DROP TYPE IF EXISTS sessiontypes;"))
    connection.execute(text("DROP TYPE IF EXISTS kernelrole;"))

    # Update `sessions.session_type` column
    kernels = sa.Table(
        "kernels",
        mapper_registry.metadata,
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", GUID),
        sa.Column(
            "role",
            postgresql.ENUM("INFERENCE", "COMPUTE", "SYSTEM", name="kernelrole"),
            default=KernelRole.COMPUTE,
            server_default=KernelRole.COMPUTE.name,
        ),
        sa.Column(
            "session_type",
            sa.VARCHAR,
            index=True,
            nullable=False,
            default="interactive",
            server_default="interactive",
        ),
        extend_existing=True,
    )

    sessions = sa.Table(
        "sessions",
        mapper_registry.metadata,
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "session_type",
            sa.VARCHAR,
            index=True,
            nullable=False,
            default="interactive",
            server_default="interactive",
        ),
        extend_existing=True,
    )
    while True:
        _sid_query = (
            sa.select(kernels.c.session_id).where(kernels.c.role == "SYSTEM").limit(PAGE_SIZE)
        )
        session_ids = cast(list[uuid.UUID], connection.scalars(_sid_query).all())
        _session_query = (
            sa.update(sessions)
            .values({"session_type": "SYSTEM"})
            .where(sessions.c.id.in_(session_ids))
        )
        _kernel_query = (
            sa.update(kernels)
            .values({"session_type": "SYSTEM", "role": "COMPUTE"})
            .where(kernels.c.session_id.in_(session_ids))
        )
        connection.execute(_session_query)
        result = connection.execute(_kernel_query)

        if result.rowcount == 0:
            break

    op.drop_column("kernels", "role")


def downgrade():
    connection = op.get_bind()

    kernel_role_values = ["INFERENCE", "COMPUTE", "SYSTEM"]
    KernelRoleType = postgresql.ENUM(*kernel_role_values, name="kernelrole")
    KernelRoleType.create(connection)
    op.add_column(
        "kernels",
        sa.Column(
            "role",
            KernelRoleType,
            autoincrement=False,
            nullable=True,
            server_default=KernelRole.COMPUTE.name,
        ),
    )

    kernels = sa.Table(
        "kernels",
        mapper_registry.metadata,
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "role",
            KernelRoleType,
            default=KernelRole.COMPUTE,
            server_default=KernelRole.COMPUTE.name,
        ),
        sa.Column(
            "session_type",
            sa.VARCHAR,
            index=True,
            nullable=False,
            default="interactive",
            server_default="interactive",
        ),
        extend_existing=True,
    )

    sessions = sa.Table(
        "sessions",
        mapper_registry.metadata,
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "session_type",
            sa.VARCHAR,
            index=True,
            nullable=False,
            default="interactive",
            server_default="interactive",
        ),
        extend_existing=True,
    )

    # replace session_type.system role
    while True:
        _sid_query = (
            sa.select(kernels.c.session_id)
            .where(kernels.c.session_type == "SYSTEM")
            .limit(PAGE_SIZE)
        )
        session_ids = cast(list[uuid.UUID], connection.scalars(_sid_query).all())
        _session_query = (
            sa.update(sessions)
            .values({"session_type": "INTERACTIVE"})
            .where(sessions.c.id.in_(session_ids))
        )
        _kernel_query = (
            sa.update(kernels)
            .values({"session_type": "INTERACTIVE", "role": "SYSTEM"})
            .where(kernels.c.session_id.in_(session_ids))
        )
        connection.execute(_session_query)
        result = connection.execute(_kernel_query)
        if result.rowcount == 0:
            break

    op.alter_column("kernels", column_name="role", nullable=False)

    connection.execute(
        text(
            "CREATE TYPE sessiontypes AS ENUM (%s)"
            % (",".join(f"'{choice.name}'" for choice in OldSessionTypes))
        )
    )
    # Revert sessions.session_type to enum
    connection.execute(text("ALTER TABLE sessions ALTER COLUMN session_type DROP DEFAULT;"))
    connection.execute(
        text(
            "ALTER TABLE sessions ALTER COLUMN session_type TYPE sessiontypes "
            "USING session_type::sessiontypes;"
        )
    )
    connection.execute(
        text("ALTER TABLE sessions ALTER COLUMN session_type SET DEFAULT 'INTERACTIVE';")
    )

    # Revert kernels.session_type to enum
    connection.execute(text("ALTER TABLE kernels ALTER COLUMN session_type DROP DEFAULT;"))
    connection.execute(
        text(
            "ALTER TABLE kernels ALTER COLUMN session_type TYPE sessiontypes "
            "USING session_type::sessiontypes;"
        )
    )
    connection.execute(
        text("ALTER TABLE kernels ALTER COLUMN session_type SET DEFAULT 'INTERACTIVE';")
    )
