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
    # After a downgrade round-trip, values are always plain numbers (int or
    # float such as 0.0, 1.0) because the downgrade converts percent values
    # to rounded integers.  We always convert to {"count": N} here.
    op.execute(
        """
        UPDATE deployment_policies
        SET strategy_spec = jsonb_set(
            strategy_spec,
            '{max_surge}',
            jsonb_build_object('count', round((strategy_spec ->> 'max_surge')::numeric)::int)
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
            jsonb_build_object('count', round((strategy_spec ->> 'max_unavailable')::numeric)::int)
        )
        WHERE strategy_spec IS NOT NULL
          AND jsonb_typeof(strategy_spec -> 'max_unavailable') = 'number'
        """
    )


def downgrade() -> None:
    # Convert IntOrPercent dict back to a plain integer.
    # count is used as-is; percent is rounded to the nearest integer so that
    # the old RollingUpdateSpec(max_surge: int) can parse the value without
    # a Pydantic validation error.
    op.execute(
        """
        UPDATE deployment_policies
        SET strategy_spec = jsonb_set(
            strategy_spec,
            '{max_surge}',
            CASE
                WHEN (strategy_spec -> 'max_surge' ->> 'count') IS NOT NULL
                    THEN to_jsonb((strategy_spec -> 'max_surge' ->> 'count')::int)
                WHEN (strategy_spec -> 'max_surge' ->> 'percent') IS NOT NULL
                    THEN to_jsonb(round((strategy_spec -> 'max_surge' ->> 'percent')::numeric)::int)
                ELSE '0'::jsonb
            END
        )
        WHERE strategy_spec IS NOT NULL
          AND jsonb_typeof(strategy_spec -> 'max_surge') = 'object'
        """
    )
    op.execute(
        """
        UPDATE deployment_policies
        SET strategy_spec = jsonb_set(
            strategy_spec,
            '{max_unavailable}',
            CASE
                WHEN (strategy_spec -> 'max_unavailable' ->> 'count') IS NOT NULL
                    THEN to_jsonb((strategy_spec -> 'max_unavailable' ->> 'count')::int)
                WHEN (strategy_spec -> 'max_unavailable' ->> 'percent') IS NOT NULL
                    THEN to_jsonb(round((strategy_spec -> 'max_unavailable' ->> 'percent')::numeric)::int)
                ELSE '0'::jsonb
            END
        )
        WHERE strategy_spec IS NOT NULL
          AND jsonb_typeof(strategy_spec -> 'max_unavailable') = 'object'
        """
    )
