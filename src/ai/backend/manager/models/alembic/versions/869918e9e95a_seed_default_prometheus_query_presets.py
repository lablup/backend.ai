"""seed_default_prometheus_query_presets

Revision ID: 869918e9e95a
Revises: 17b679c98b50
Create Date: 2026-03-15 00:00:00.000000

"""

import json
import textwrap
from typing import Any

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "869918e9e95a"
down_revision = "17b679c98b50"
branch_labels = None
depends_on = None

FILTER_LABELS = [
    "container_metric_name",
    "kernel_id",
    "session_id",
    "agent_id",
    "user_id",
    "project_id",
    "value_type",
]

GROUP_LABELS = [
    "kernel_id",
    "session_id",
    "agent_id",
    "user_id",
    "project_id",
    "value_type",
]

PRESETS: list[dict[str, Any]] = [
    {
        "name": "container_gauge",
        "metric_name": "backendai_container_utilization",
        "query_template": "sum by ({group_by})(backendai_container_utilization{{{labels}}})",
        "time_window": None,
        "options": json.dumps({"filter_labels": FILTER_LABELS, "group_labels": GROUP_LABELS}),
    },
    {
        "name": "container_rate",
        "metric_name": "backendai_container_utilization",
        "query_template": (
            "sum by ({group_by})(rate(backendai_container_utilization{{{labels}}}[{window}])) / 5.0"
        ),
        "time_window": "5m",
        "options": json.dumps({"filter_labels": FILTER_LABELS, "group_labels": GROUP_LABELS}),
    },
    {
        "name": "container_diff",
        "metric_name": "backendai_container_utilization",
        "query_template": (
            "sum by ({group_by})(rate(backendai_container_utilization{{{labels}}}[{window}]))"
        ),
        "time_window": "5m",
        "options": json.dumps({"filter_labels": FILTER_LABELS, "group_labels": GROUP_LABELS}),
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    for preset in PRESETS:
        conn.execute(
            sa.text(
                textwrap.dedent("""\
                    INSERT INTO prometheus_query_presets
                        (name, metric_name, query_template, time_window, options)
                    SELECT :name, :metric_name, :query_template, :time_window, CAST(:options AS jsonb)
                    WHERE NOT EXISTS (
                        SELECT 1 FROM prometheus_query_presets WHERE name = CAST(:name AS varchar)
                    )
                """)
            ),
            parameters=preset,
        )


def downgrade() -> None:
    # Data-only migration: seeded rows are not removed on downgrade
    # to avoid deleting user-modified presets that share the same name.
    pass
