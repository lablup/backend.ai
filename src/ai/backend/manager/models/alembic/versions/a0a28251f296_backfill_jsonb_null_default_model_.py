"""backfill jsonb null default_model_definition in runtime_variants

Runtime variants created through the create API stored a JSON ``null`` in
``runtime_variants.default_model_definition``: the creator never set the
attribute and SQLAlchemy's JSON type serializes Python ``None`` as JSON
``null`` rather than SQL ``NULL``, so it slipped past the NOT NULL
constraint. Such rows load back as ``None`` and fail the node conversion,
which requires a model definition value. The creator now seeds an empty
draft (``{}``); this migration backfills the already-materialized JSON
``null`` rows with the same empty draft. ``{}`` (not ``{"models": null}``)
keeps every field truly unset, consistent with the exclude_unset write path
established by revision 2ec0aa5a19cf.

Revision ID: a0a28251f296
Revises: e5b71c94d2a8
Create Date: 2026-07-22 09:17:13.529025

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a0a28251f296"
down_revision = "e5b71c94d2a8"
branch_labels = None
depends_on = None
# Part of: NEXT_RELEASE_VERSION


def upgrade() -> None:
    op.execute(
        "UPDATE runtime_variants"
        " SET default_model_definition = '{}'::jsonb"
        " WHERE default_model_definition = 'null'::jsonb"
    )


def downgrade() -> None:
    # The JSON null values carried no information (never-set attribute
    # artifacts), so there is nothing to restore.
    pass
