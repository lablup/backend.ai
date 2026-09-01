"""backfill project entity memberships for vfolders, endpoints and model cards

Revision ID: b41d7c92e58a
Revises: c8e4b1a09d37
Create Date: 2026-09-01 10:22:41

"""

# Part of: NEXT_RELEASE_VERSION

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b41d7c92e58a"
down_revision = "c8e4b1a09d37"
branch_labels = None
depends_on = None


_OWNED_BY_PROJECT = (
    ("vfolder", "vfolders", "group"),
    ("deployment", "endpoints", "project"),
    ("model_card", "model_cards", "project"),
)


def upgrade() -> None:
    """Record every project-owned vfolder, endpoint and model card as a member of its
    project's virtual scope, so the scoped reads can be answered from the chain instead
    of the owner column. Idempotent via ON CONFLICT.
    """
    op.execute(
        sa.text(
            """
            INSERT INTO virtual_scopes (scope_type, scope_id)
            SELECT 'project', id FROM groups
            ON CONFLICT (scope_type, scope_id) DO NOTHING
            """
        )
    )
    for entity_type, table, owner_column in _OWNED_BY_PROJECT:
        op.execute(
            sa.text(
                f"""
                INSERT INTO entity_memberships (virtual_scope_id, entity_type, entity_id)
                SELECT vs.id, :entity_type, t.id
                FROM {table} t
                JOIN virtual_scopes vs
                    ON vs.scope_type = 'project'
                    AND vs.scope_id = t."{owner_column}"
                WHERE t."{owner_column}" IS NOT NULL
                ON CONFLICT (virtual_scope_id, entity_type, entity_id) DO NOTHING
                """
            ).bindparams(entity_type=entity_type)
        )


def downgrade() -> None:
    """Drop only the edges this revision adds: the project-scope membership of the three
    entity types. Edges written by the create path carry no marker distinguishing them,
    so a re-upgrade restores what a downgrade removed.
    """
    for entity_type, table, owner_column in _OWNED_BY_PROJECT:
        op.execute(
            sa.text(
                f"""
                DELETE FROM entity_memberships em
                USING virtual_scopes vs, {table} t
                WHERE em.virtual_scope_id = vs.id
                    AND em.entity_type = :entity_type
                    AND em.entity_id = t.id
                    AND vs.scope_type = 'project'
                    AND vs.scope_id = t."{owner_column}"
                """
            ).bindparams(entity_type=entity_type)
        )
