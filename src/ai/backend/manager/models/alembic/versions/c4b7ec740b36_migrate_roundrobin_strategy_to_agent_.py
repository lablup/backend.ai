"""migrate-roundrobin-strategy-to-agent-selector-config

Revision ID: c4b7ec740b36
Revises: 59a622c31820
Create Date: 2024-09-17 00:31:31.379466

"""

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "c4b7ec740b36"
down_revision = "59a622c31820"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        text("""
    UPDATE scaling_groups
    SET scheduler_opts =
    CASE
        WHEN scheduler_opts ? 'roundrobin' AND scheduler_opts->>'roundrobin' = 'true' THEN
            jsonb_set(
                jsonb_set(
                    scheduler_opts - 'roundrobin',
                    '{agent_selection_strategy}', '"roundrobin"'::jsonb
                ),
                '{agent_selector_config}', '{}'::jsonb
            )
        ELSE jsonb_set(
            scheduler_opts - 'roundrobin',
            '{agent_selector_config}', '{}'::jsonb
        )
    END;
    """)
    )


def downgrade() -> None:
    op.execute(
        text("""
    UPDATE scaling_groups
    SET scheduler_opts =
    CASE
        WHEN scheduler_opts->>'agent_selection_strategy' = 'roundrobin' THEN
            jsonb_set(
                jsonb_set(
                    scheduler_opts - 'agent_selector_config',
                    '{agent_selection_strategy}', '"legacy"'::jsonb
                ),
                '{roundrobin}', 'true'::jsonb
            )
        ELSE scheduler_opts - 'agent_selector_config'
    END;
    """)
    )
