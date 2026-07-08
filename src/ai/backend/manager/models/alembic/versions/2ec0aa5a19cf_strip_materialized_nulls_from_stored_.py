"""strip materialized nulls from stored model definitions

Stored model definitions were serialized with plain ``model_dump()``,
materializing every unset optional field as an explicit ``null`` key.
Re-parsing such JSON marks those fields as "explicitly set" in
``model_fields_set``, which defeats the draft-side default injection in
``ModelServiceConfigDraft.to_resolved()`` (most visibly: ``service.shell``
resolves to ``null`` instead of ``/bin/bash``, so string start-commands are
shlex-split instead of run under a shell).

``jsonb_strip_nulls`` removes null-valued object keys at every nesting
level so unset fields become truly absent. Nulls in these rows are
serializer artifacts, not user intent — writes now use ``exclude_unset``
dumps so intentional explicit nulls survive from here on.

Revision ID: 2ec0aa5a19cf
Revises: c05f9465a9cd
Create Date: 2026-07-07 14:37:50.082414

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "2ec0aa5a19cf"
down_revision = "c05f9465a9cd"
branch_labels = None
depends_on = None
# Part of: NEXT_RELEASE_VERSION


def upgrade() -> None:
    op.execute(
        "UPDATE runtime_variants"
        " SET default_model_definition = jsonb_strip_nulls(default_model_definition)"
    )
    op.execute(
        "UPDATE deployment_revision_presets"
        " SET model_definition = jsonb_strip_nulls(model_definition)"
        " WHERE model_definition IS NOT NULL"
    )
    op.execute(
        "UPDATE deployment_revisions"
        " SET model_definition = jsonb_strip_nulls(model_definition)"
        " WHERE model_definition IS NOT NULL"
    )


def downgrade() -> None:
    # Lossy normalization: the stripped null keys carried no information
    # (unset-as-null artifacts), so there is nothing to restore.
    pass
