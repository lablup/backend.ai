"""migrate strategy_spec legacy plain-int values to IntOrPercent dict format

Revision ID: bbcc151ec870
Revises: e3111d960208
Create Date: 2026-04-02

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "bbcc151ec870"
down_revision = "e3111d960208"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The original create_deployment_policies migration (4c9e2f3a5b6d) seeded
    # strategy_spec with plain integers:
    #   {"max_surge": 1, "max_unavailable": 0}
    #
    # The IntOrPercent model now expects:
    #   {"max_surge": {"count": 1}, "max_unavailable": {"count": 0}}
    #
    # Convert any rows where max_surge or max_unavailable is a plain integer
    # to the new {"count": N} dict format.
    op.execute(
        """
        UPDATE deployment_policies
        SET strategy_spec = jsonb_set(
            strategy_spec,
            '{max_surge}',
            jsonb_build_object('count', (strategy_spec ->> 'max_surge')::int)
        )
        WHERE strategy_spec IS NOT NULL
          AND jsonb_typeof(strategy_spec -> 'max_surge') = 'number'
        """
    )
    op.execute(
        """
        UPDATE deployment_policies
        SET strategy_spec = jsonb_set(
            strategy_spec,
            '{max_unavailable}',
            jsonb_build_object('count', (strategy_spec ->> 'max_unavailable')::int)
        )
        WHERE strategy_spec IS NOT NULL
          AND jsonb_typeof(strategy_spec -> 'max_unavailable') = 'number'
        """
    )


def downgrade() -> None:
    # Convert back to plain integer format
    op.execute(
        """
        UPDATE deployment_policies
        SET strategy_spec = jsonb_set(
            strategy_spec,
            '{max_surge}',
            to_jsonb((strategy_spec -> 'max_surge' ->> 'count')::int)
        )
        WHERE strategy_spec IS NOT NULL
          AND jsonb_typeof(strategy_spec -> 'max_surge') = 'object'
          AND strategy_spec -> 'max_surge' ? 'count'
        """
    )
    op.execute(
        """
        UPDATE deployment_policies
        SET strategy_spec = jsonb_set(
            strategy_spec,
            '{max_unavailable}',
            to_jsonb((strategy_spec -> 'max_unavailable' ->> 'count')::int)
        )
        WHERE strategy_spec IS NOT NULL
          AND jsonb_typeof(strategy_spec -> 'max_unavailable') = 'object'
          AND strategy_spec -> 'max_unavailable' ? 'count'
        """
    )
