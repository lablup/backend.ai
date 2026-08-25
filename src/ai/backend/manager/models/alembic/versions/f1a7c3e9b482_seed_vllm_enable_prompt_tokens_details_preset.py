"""seed the vLLM --enable-prompt-tokens-details preset

Adds the single ``enable-prompt-tokens-details`` row for the ``vllm`` runtime
variant. ``e7b3a1f9c2d4`` seeded the rest of the presets but has already been
stamped on every existing install, so a new revision is the only way the row
reaches a running cluster.

Revision ID: f1a7c3e9b482
Revises: e7b2c9f04d31
Create Date: 2026-08-19

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f1a7c3e9b482"
down_revision = "e7b2c9f04d31"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.get_bind().execute(
        sa.text("""
            INSERT INTO runtime_variant_presets
                (runtime_variant, name, description, rank, preset_target, value_type,
                 default_value, key, category, display_name, ui_option)
            SELECT
                rv.id,
                'enable-prompt-tokens-details',
                'Report prompt token details (e.g. prefix cache hits) in usage.',
                3000,
                'args',
                'flag',
                NULL,
                '--enable-prompt-tokens-details',
                'monitoring',
                'Enable Prompt Tokens Details',
                CAST('{"ui_type": "checkbox"}' AS JSONB)
            FROM runtime_variants rv
            WHERE rv.name = 'vllm'
            ON CONFLICT ON CONSTRAINT uq_runtime_variant_presets_variant_name DO NOTHING
        """)
    )


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("""
            DELETE FROM runtime_variant_presets
            WHERE name = 'enable-prompt-tokens-details'
              AND runtime_variant = (SELECT id FROM runtime_variants WHERE name = 'vllm')
        """)
    )
