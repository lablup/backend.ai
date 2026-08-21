"""mark the default keypair resource policy

Which policy a new keypair gets was decided by a name the source held
(``DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME``), so renaming or removing that row left
the code pointing at nothing. The table says it instead.

Exactly one row carries the mark once this has run: the partial unique index caps
it at one, and the backfill leaves none uncovered — it marks ``default`` if that
row is there, else the oldest policy, else it inserts one.

Revision ID: b7e4c2058fa1
Revises: a3f19d6c74b2
Create Date: 2026-08-21 09:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7e4c2058fa1"
down_revision = "a3f19d6c74b2"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None

_SEEDED_DEFAULT = {
    "name": "default",
    "default_for_unspecified": "UNLIMITED",
    "total_resource_slots": "{}",
    "max_session_lifetime": 0,
    "max_concurrent_sessions": 30,
    "max_concurrent_sftp_sessions": 1,
    "max_containers_per_session": 1,
    "idle_timeout": 3600,
    "allowed_vfolder_hosts": "{}",
}


def upgrade() -> None:
    op.add_column(
        "keypair_resource_policies",
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "uq_keypair_resource_policies_is_default",
        "keypair_resource_policies",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default"),
    )

    conn = op.get_bind()
    # The row the source used to name, if the installation still has it.
    marked = conn.execute(
        sa.text(
            "UPDATE keypair_resource_policies SET is_default = true"
            " WHERE name = 'default' RETURNING name"
        )
    ).first()
    if marked is not None:
        return

    # Otherwise the oldest policy takes the mark, so an installation that renamed
    # the row keeps creating keypairs.
    marked = conn.execute(
        sa.text(
            "UPDATE keypair_resource_policies SET is_default = true WHERE name = ("
            " SELECT name FROM keypair_resource_policies ORDER BY created_at, name LIMIT 1"
            ") RETURNING name"
        )
    ).first()
    if marked is not None:
        return

    # An installation with no policy at all gets one, since a keypair needs it.
    conn.execute(
        sa.text(
            "INSERT INTO keypair_resource_policies ("
            " name, is_default, default_for_unspecified, total_resource_slots,"
            " max_session_lifetime, max_concurrent_sessions, max_concurrent_sftp_sessions,"
            " max_containers_per_session, idle_timeout, allowed_vfolder_hosts"
            ") VALUES ("
            " :name, true, :default_for_unspecified, :total_resource_slots,"
            " :max_session_lifetime, :max_concurrent_sessions, :max_concurrent_sftp_sessions,"
            " :max_containers_per_session, :idle_timeout, :allowed_vfolder_hosts"
            ")"
        ),
        _SEEDED_DEFAULT,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_keypair_resource_policies_is_default",
        table_name="keypair_resource_policies",
    )
    op.drop_column("keypair_resource_policies", "is_default")
