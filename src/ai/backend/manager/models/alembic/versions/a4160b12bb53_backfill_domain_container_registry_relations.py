"""Relate each domain to the container registries its allowed_docker_registries names.

A name matches every registry whose registry_name is that name.
The allowed_docker_registries column is left in place.
"""

import sqlalchemy as sa
from alembic import op

revision = "a4160b12bb53"  # Part of: NEXT_RELEASE_VERSION
down_revision = "ba3e3ab0d354"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A pair already related is skipped, so re-running is a no-op.
    op.execute(
        sa.text("""
        INSERT INTO domain_container_registry_relations (domain_id, container_registry_id)
        SELECT d.id, cr.id
        FROM domains AS d
        JOIN container_registries AS cr ON cr.registry_name = ANY(d.allowed_docker_registries)
        ON CONFLICT DO NOTHING
    """)
    )


def downgrade() -> None:
    # A relation written after the upgrade cannot be told apart from a backfilled one.
    pass
