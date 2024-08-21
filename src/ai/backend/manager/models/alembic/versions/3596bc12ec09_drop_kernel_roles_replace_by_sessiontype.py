"""replace_kernelrole_to_sessiontypes

Revision ID: 3596bc12ec09
Revises: 59a622c31820
Create Date: 2023-10-04 16:43:46.281383

"""

import enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy import cast
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text
from sqlalchemy.sql.functions import coalesce

from ai.backend.manager.models.base import GUID, EnumType, mapper_registry

# revision identifiers, used by Alembic.
revision = "3596bc12ec09"
down_revision = "59a622c31820"
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
    op.drop_column("kernels", "role")

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

    connection.execute(text("DROP TYPE sessiontypes;"))


def downgrade():
    connection = op.get_bind()
    op.add_column(
        "kernels",
        sa.Column(
            "role",
            postgresql.ENUM("INFERENCE", "COMPUTE", "SYSTEM", name="kernelrole"),
            autoincrement=False,
            nullable=True,
        ),
    )

    kernels = sa.Table(
        "kernels",
        mapper_registry.metadata,
        sa.Column("id", GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")),
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

    # replace session_type.system role
    while True:
        _subq = sa.select([kernels.c.id]).where(kernels.c.session_type == "system").limit(PAGE_SIZE)
        _fetch_query = (
            sa.update(kernels).values({"session_type": "batch"}).where(kernels.c.id.in_(_subq))
        )
        result = connection.execute(_fetch_query)
        if result.rowcount < PAGE_SIZE:
            break

    while True:
        _subq = (
            sa.select([sessions.c.id]).where(sessions.c.session_type == "system").limit(PAGE_SIZE)
        )
        _fetch_query = (
            sa.update(sessions).values({"session_type": "batch"}).where(sessions.c.id.in_(_subq))
        )
        result = connection.execute(_fetch_query)
        if result.rowcount < PAGE_SIZE:
            break

    images = sa.Table(
        "images",
        mapper_registry.metadata,
        sa.Column("name", sa.String, nullable=False, index=True),
        sa.Column("labels", sa.JSON, nullable=False),
        extend_existing=True,
    )

    kernelrole.create(connection)

    batch_size = 1000
    total_rowcount = 0
    while True:
        # Fetch records whose `role` is null only. This removes the use of offset from the query.
        # `order_by` is not necessary, but helpful to display the currently processing kernels.
        query = (
            sa.select([kernels.c.id])
            .where(kernels.c.role.is_(None))
            .order_by(kernels.c.id)
            .limit(batch_size)
        )
        result = connection.execute(query).fetchall()
        kernel_ids_to_update = [kid[0] for kid in result]

        if not kernel_ids_to_update:
            break
        query = (
            sa.update(kernels)
            .values({
                "role": cast(
                    coalesce(
                        # `limit(1)` is introduced since it is possible (not prevented) for two
                        # records have the same image name. Without `limit(1)`, the records
                        # raises multiple values error.
                        sa.select([images.c.labels.op("->>")("ai.backend.role")])
                        .select_from(images)
                        .where(images.c.name == kernels.c.image)
                        .limit(1)
                        .as_scalar(),
                        # Set the default role when there is no matching image.
                        # This may occur when one of the previously used image is deleted.
                        KernelRole.COMPUTE.value,
                    ),
                    EnumType(KernelRole),
                )
            })
            .where(kernels.c.id.in_(kernel_ids_to_update))
        )
        result = connection.execute(query)
        total_rowcount += result.rowcount
        print(f"total processed count: {total_rowcount} (~{kernel_ids_to_update[-1]})")

        if result.rowcount < batch_size:
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
