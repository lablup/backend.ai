"""record a project's creating user and backfill a personal project per user

Adds ``groups.creator_id`` — provenance, not ownership, which stays the
scope-virtual entity-entity path alone — and the partial unique index holding a user
to at most one personal project. The column is nulled when its user goes, leaving the
project dangling for the retention sweep.

The backfill writes the project rows only. Their graph rows (virtual entity, the
domain's own and govern edges, the roster) come with the one ownership-data migration,
which provisions them for every entity at once.

Revision ID: c7a4f1e9b023
Revises: d5b3f8c26a41
Create Date: 2026-09-05 15:10:00

"""

# Part of: NEXT_RELEASE_VERSION

import re
from typing import Final

import sqlalchemy as sa
from alembic import op

from ai.backend.manager.models.base import GUID

# revision identifiers, used by Alembic.
revision = "c7a4f1e9b023"
down_revision = "d5b3f8c26a41"
branch_labels = None
depends_on = None

# The project name column takes a slug: word characters, dots and hyphens, with no
# run of separators and none at either edge. The tail is left free for the suffix a
# name already taken in the domain needs.
_NON_SLUG_CHARS: Final = re.compile(r"[^\w.-]")
_SEPARATOR_RUN: Final = re.compile(r"[._-]{2,}")
_EDGE_CHARS: Final = "._-"
_NAME_BASE_LIMIT: Final = 60
_NAME_SUFFIX_LIMIT: Final = 1000

# An empty msgpack list, the dotfiles column's default.
_EMPTY_DOTFILES: Final = b"\x90"

_INDEX_NAME: Final = "uq_groups_personal_creator"

_USERS_WITHOUT_A_PERSONAL_PROJECT: Final = sa.text("""
    SELECT u.uuid AS user_uuid, u.username, u.domain_name
    FROM users u
    WHERE NOT EXISTS (
        SELECT 1 FROM groups g
        WHERE g.type = 'personal' AND g.creator_id = u.uuid
    )
    ORDER BY u.created_at, u.uuid
""")

_INSERT_PROJECT: Final = sa.text("""
    INSERT INTO groups (
        name, description, is_active, domain_name,
        total_resource_slots, allowed_vfolder_hosts, dotfiles,
        resource_policy, type, creator_id
    )
    VALUES (
        :name, 'Personal Project', true, :domain_name,
        '{}'::jsonb, '{}'::jsonb, :dotfiles,
        :resource_policy, 'personal', :creator_id
    )
""")


def _slugify(value: str) -> str:
    """``value`` reduced to what the project name column accepts. Empty when nothing
    survives."""
    slug = _SEPARATOR_RUN.sub("-", _NON_SLUG_CHARS.sub("-", value))
    slug = slug.strip(_EDGE_CHARS)[:_NAME_BASE_LIMIT]
    return slug.rstrip(_EDGE_CHARS)


def _free_name(taken: set[tuple[str, str]], domain_name: str, base: str) -> str:
    """``base`` if the domain does not hold it, else the first free numeric suffix."""
    if (domain_name, base) not in taken:
        return base
    for suffix in range(2, _NAME_SUFFIX_LIMIT):
        candidate = f"{base}-{suffix}"
        if (domain_name, candidate) not in taken:
            return candidate
    raise RuntimeError(f"No free personal project name for '{base}' in domain {domain_name}")


def upgrade() -> None:
    op.add_column("groups", sa.Column("creator_id", GUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_groups_creator_id_users"),
        "groups",
        "users",
        ["creator_id"],
        ["uuid"],
        ondelete="SET NULL",
    )
    backfill(op.get_bind())
    # The index goes on after the backfill: it describes the state it produces.
    op.create_index(
        _INDEX_NAME,
        "groups",
        ["creator_id"],
        unique=True,
        postgresql_where=sa.text("type = 'personal'"),
    )


def backfill(conn: sa.Connection) -> None:
    """Create the personal project every user is missing. Takes its connection so a
    test can run it against a real database — static analysis does not reach SQL."""
    resource_policy = conn.scalar(
        sa.text("""
            SELECT name FROM project_resource_policies
            ORDER BY (name <> 'default'), name
            LIMIT 1
        """)
    )
    if resource_policy is None:
        raise RuntimeError(
            "No project resource policy exists; a personal project cannot be created without one."
        )

    users = conn.execute(_USERS_WITHOUT_A_PERSONAL_PROJECT).mappings().all()
    if not users:
        return
    taken = {
        (row.domain_name, row.name)
        for row in conn.execute(sa.text("SELECT domain_name, name FROM groups"))
    }

    for user in users:
        name = _free_name(
            taken,
            user["domain_name"],
            _slugify(user["username"]) or str(user["user_uuid"]),
        )
        taken.add((user["domain_name"], name))
        conn.execute(
            _INSERT_PROJECT,
            {
                "name": name,
                "domain_name": user["domain_name"],
                "dotfiles": _EMPTY_DOTFILES,
                "resource_policy": resource_policy,
                "creator_id": user["user_uuid"],
            },
        )


def downgrade() -> None:
    op.drop_index(_INDEX_NAME, table_name="groups")
    op.execute(sa.text("DELETE FROM groups WHERE type = 'personal'"))
    op.drop_constraint(op.f("fk_groups_creator_id_users"), "groups", type_="foreignkey")
    op.drop_column("groups", "creator_id")
