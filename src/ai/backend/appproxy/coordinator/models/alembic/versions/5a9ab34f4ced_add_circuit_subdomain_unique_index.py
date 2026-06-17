"""add partial unique index for circuit subdomain per worker

Revision ID: 5a9ab34f4ced
Revises: a1b2c3d4e5f6
Create Date: 2026-06-17 00:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "5a9ab34f4ced"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # In wildcard mode the URL is ``{subdomain}{worker.wildcard_domain}``, so a
    # subdomain must be unique per worker.
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_circuits_worker_subdomain "
        "ON circuits (worker, subdomain) "
        "WHERE frontend_mode = 'WILDCARD_DOMAIN'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_circuits_worker_subdomain")
