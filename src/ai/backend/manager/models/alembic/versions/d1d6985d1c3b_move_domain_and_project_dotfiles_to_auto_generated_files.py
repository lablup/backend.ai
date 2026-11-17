"""Move domain and project dotfiles to auto-generated files

Each entry of `domains.dotfiles` and `groups.dotfiles` becomes a file the domain or project
owns, as the default of its path, with its data as revision 1 and its graph node. The columns
stay, unread, until a later migration drops them.

Revision ID: d1d6985d1c3b
Revises: 75cc7e8fc4d2
Create Date: 2026-11-16

"""

from __future__ import annotations

import msgpack
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d1d6985d1c3b"  # Part of: NEXT_RELEASE_VERSION
down_revision = "75cc7e8fc4d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    owners = conn.execute(
        sa.text("""
            SELECT 'domain' AS entity_type, id, dotfiles FROM domains
            UNION ALL
            SELECT 'project' AS entity_type, id, dotfiles FROM groups
        """)
    ).all()
    for entity_type, owner_id, dotfiles in owners:
        if not dotfiles:
            continue
        default_paths: set[str] = set()
        for entry in msgpack.unpackb(dotfiles, raw=False) or []:
            # Text cannot hold NUL.
            path, perm, data = (
                entry[field].replace("\x00", "") for field in ("path", "perm", "data")
            )
            # A repeated path, which only a raw column write could leave, becomes a variant.
            is_default = path not in default_paths
            default_paths.add(path)
            file_id = conn.execute(
                sa.text("""
                    INSERT INTO auto_generated_files
                        (entity_type, entity_id, path, perm, is_default)
                    VALUES (:entity_type, :entity_id, :path, :perm, :is_default)
                    RETURNING id
                """),
                {
                    "entity_type": entity_type,
                    "entity_id": owner_id,
                    "path": path,
                    "perm": perm,
                    "is_default": is_default,
                },
            ).scalar_one()
            conn.execute(
                sa.text("""
                    INSERT INTO auto_generated_file_revisions (file_id, revision_number, data)
                    VALUES (:file_id, 1, :data)
                """),
                {"file_id": file_id, "data": data},
            )
    # Give each new file a node owning and governing itself, owned and governed by its owner.
    conn.execute(
        sa.text("""
            INSERT INTO virtual_entities (entity_type, entity_id)
            SELECT 'auto_generated_file', id FROM auto_generated_files
            ON CONFLICT (entity_type, entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text("""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT id, id, FALSE FROM virtual_entities
            WHERE entity_type = 'auto_generated_file'
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text("""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT id, id, NULL FROM virtual_entities
            WHERE entity_type = 'auto_generated_file'
            ON CONFLICT DO NOTHING
        """)
    )
    file_and_owner_nodes = """
        SELECT file_node.id AS file_node, owner_node.id AS owner_node
        FROM auto_generated_files f
        JOIN virtual_entities file_node
          ON file_node.entity_type = 'auto_generated_file' AND file_node.entity_id = f.id
        JOIN virtual_entities owner_node
          ON owner_node.entity_type = f.entity_type AND owner_node.entity_id = f.entity_id
    """
    conn.execute(
        sa.text(f"""
            INSERT INTO entity_memberships (virtual_entity_id, member_entity_id, capped)
            SELECT n.owner_node, n.file_node, FALSE FROM ({file_and_owner_nodes}) n
            ON CONFLICT (virtual_entity_id, member_entity_id) DO NOTHING
        """)
    )
    conn.execute(
        sa.text(f"""
            INSERT INTO scope_bindings (virtual_entity_id, scope_entity_id, permission_cap)
            SELECT n.file_node, n.owner_node, NULL FROM ({file_and_owner_nodes}) n
            ON CONFLICT DO NOTHING
        """)
    )


def downgrade() -> None:
    conn = op.get_bind()
    files = conn.execute(
        sa.text("""
            SELECT DISTINCT ON (f.id) f.entity_type, f.entity_id AS owner, f.path, f.perm, r.data
            FROM auto_generated_files f
            JOIN auto_generated_file_revisions r ON r.file_id = f.id
            WHERE f.entity_type IN ('domain', 'project') AND f.is_default
            ORDER BY f.id, r.revision_number DESC
        """)
    ).all()
    entries: dict[tuple[str, object], list[dict[str, str]]] = {}
    for file in files:
        entries.setdefault((file.entity_type, file.owner), []).append({
            "path": file.path,
            "perm": file.perm,
            "data": file.data,
        })
    # Every owner is written, so one whose files were all removed gets an empty list.
    conn.execute(sa.text("UPDATE domains SET dotfiles = :empty"), {"empty": b"\x90"})
    conn.execute(sa.text("UPDATE groups SET dotfiles = :empty"), {"empty": b"\x90"})
    for (entity_type, owner), owned in entries.items():
        table = "domains" if entity_type == "domain" else "groups"
        conn.execute(
            sa.text(f"UPDATE {table} SET dotfiles = :dotfiles WHERE id = :owner"),
            {"owner": owner, "dotfiles": msgpack.packb(owned, use_bin_type=True)},
        )
    # Removing a file node removes its edges; removing the file removes its revisions.
    conn.execute(
        sa.text("""
            DELETE FROM virtual_entities
            WHERE entity_type = 'auto_generated_file'
              AND entity_id IN (
                SELECT id FROM auto_generated_files WHERE entity_type IN ('domain', 'project')
              )
        """)
    )
    conn.execute(
        sa.text("DELETE FROM auto_generated_files WHERE entity_type IN ('domain', 'project')")
    )
