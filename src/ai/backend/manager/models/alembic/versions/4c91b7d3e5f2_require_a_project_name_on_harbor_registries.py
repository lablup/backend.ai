"""Require a project name on Harbor registries

A Harbor registry addresses images through a project, so a row of that type without a
project name, or with one Harbor would reject, cannot be used. The manager checked this
in Python on the way in, which left the rule to whichever code path happened to run it;
the column now carries it, so every writer answers to the same rule.

Rows already stored are not rewritten. A Harbor row that fails the condition makes this
migration stop, and the operator fixes the row before running it again — the registry it
names does not work in that state either way.

Revision ID: 4c91b7d3e5f2
Revises: f7b1e5a9032c
Create Date: 2026-10-01

"""

from __future__ import annotations

from typing import Final

import sqlalchemy as sa
from alembic import op

revision = "4c91b7d3e5f2"  # Part of: NEXT_RELEASE_VERSION
down_revision = "f7b1e5a9032c"
branch_labels = None
depends_on = None

_CONSTRAINT_NAME: Final = "ck_container_registries_harbor_project"
_CONDITION: Final = (
    "type NOT IN ('harbor', 'harbor2')"
    " OR (project IS NOT NULL AND project ~ '^[a-z0-9]+([._-][a-z0-9]+)*$')"
)


def upgrade() -> None:
    offenders = (
        op.get_bind()
        .execute(
            sa.text(f"""
                SELECT id, registry_name, project
                FROM container_registries
                WHERE NOT ({_CONDITION})
            """)
        )
        .fetchall()
    )
    if offenders:
        listed = ", ".join(
            f"{row.registry_name} (id={row.id}, project={row.project!r})" for row in offenders
        )
        raise RuntimeError(
            "These Harbor registries carry a project name Harbor would reject, so the"
            f" constraint cannot be added. Fix or remove them, then run this again: {listed}"
        )

    op.execute(f"""
        ALTER TABLE container_registries
            DROP CONSTRAINT IF EXISTS {_CONSTRAINT_NAME}
    """)
    op.create_check_constraint(
        op.f(_CONSTRAINT_NAME),
        "container_registries",
        _CONDITION,
    )


def downgrade() -> None:
    op.execute(f"""
        ALTER TABLE container_registries
            DROP CONSTRAINT IF EXISTS {_CONSTRAINT_NAME}
    """)
