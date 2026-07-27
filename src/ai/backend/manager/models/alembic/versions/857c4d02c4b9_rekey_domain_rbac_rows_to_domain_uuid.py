"""rekey domain rbac rows to domain uuid

Legacy RBAC tables (``association_scopes_entities``, ``permissions``) keyed
Domain scope rows by the domain name. The virtual-scope chain requires UUID
keys, so domain-keyed rows are converted to the canonical string form of
``domains.id``.

Also provisions the virtual-scope chain for existing domains:
- a ``virtual_scopes`` node per domain with its self entity-membership and
  self scope-binding (mirroring ``RBACWriteOps._insert_virtual_scopes``),
- a binding of each domain into its projects' virtual scopes (mirroring what
  project creation now writes),
- an entity-membership of each user in its domain's virtual scope.

Every statement is idempotent: name-keyed rows are matched via a join on
``domains.name`` (already-converted rows no longer match), converted rows
that would collide with an existing UUID-keyed duplicate are dropped instead,
and all inserts use ``ON CONFLICT DO NOTHING``.

Revision ID: 857c4d02c4b9
Revises: c4e1a7f9b26d
Create Date: 2026-07-27 15:42:17.472002

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "857c4d02c4b9"
down_revision = "c4e1a7f9b26d"
# Part of: NEXT_RELEASE_VERSION
branch_labels = None
depends_on = None


def _rekey_name_to_uuid() -> None:
    conn = op.get_bind()
    # association_scopes_entities: domain as scope.
    conn.execute(
        sa.text("""
            UPDATE association_scopes_entities ase
            SET scope_id = d.id::text
            FROM domains d
            WHERE ase.scope_type = 'domain'
              AND ase.scope_id = d.name
              AND NOT EXISTS (
                  SELECT 1 FROM association_scopes_entities dup
                  WHERE dup.scope_type = 'domain'
                    AND dup.scope_id = d.id::text
                    AND dup.entity_id = ase.entity_id
              )
        """)
    )
    # Leftover name-keyed rows are duplicates of already-converted rows.
    conn.execute(
        sa.text("""
            DELETE FROM association_scopes_entities ase
            USING domains d
            WHERE ase.scope_type = 'domain'
              AND ase.scope_id = d.name
        """)
    )
    # association_scopes_entities: domain as entity.
    conn.execute(
        sa.text("""
            UPDATE association_scopes_entities ase
            SET entity_id = d.id::text
            FROM domains d
            WHERE ase.entity_type = 'domain'
              AND ase.entity_id = d.name
              AND NOT EXISTS (
                  SELECT 1 FROM association_scopes_entities dup
                  WHERE dup.scope_type = ase.scope_type
                    AND dup.scope_id = ase.scope_id
                    AND dup.entity_id = d.id::text
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM association_scopes_entities ase
            USING domains d
            WHERE ase.entity_type = 'domain'
              AND ase.entity_id = d.name
        """)
    )
    # permissions: domain as scope.
    conn.execute(
        sa.text("""
            UPDATE permissions p
            SET scope_id = d.id::text
            FROM domains d
            WHERE p.scope_type = 'domain'
              AND p.scope_id = d.name
              AND NOT EXISTS (
                  SELECT 1 FROM permissions dup
                  WHERE dup.role_id = p.role_id
                    AND dup.scope_type = 'domain'
                    AND dup.scope_id = d.id::text
                    AND dup.entity_type = p.entity_type
                    AND dup.operation = p.operation
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING domains d
            WHERE p.scope_type = 'domain'
              AND p.scope_id = d.name
        """)
    )


def _rekey_uuid_to_name() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE association_scopes_entities ase
            SET scope_id = d.name
            FROM domains d
            WHERE ase.scope_type = 'domain'
              AND ase.scope_id = d.id::text
              AND NOT EXISTS (
                  SELECT 1 FROM association_scopes_entities dup
                  WHERE dup.scope_type = 'domain'
                    AND dup.scope_id = d.name
                    AND dup.entity_id = ase.entity_id
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM association_scopes_entities ase
            USING domains d
            WHERE ase.scope_type = 'domain'
              AND ase.scope_id = d.id::text
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE association_scopes_entities ase
            SET entity_id = d.name
            FROM domains d
            WHERE ase.entity_type = 'domain'
              AND ase.entity_id = d.id::text
              AND NOT EXISTS (
                  SELECT 1 FROM association_scopes_entities dup
                  WHERE dup.scope_type = ase.scope_type
                    AND dup.scope_id = ase.scope_id
                    AND dup.entity_id = d.name
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM association_scopes_entities ase
            USING domains d
            WHERE ase.entity_type = 'domain'
              AND ase.entity_id = d.id::text
        """)
    )
    conn.execute(
        sa.text("""
            UPDATE permissions p
            SET scope_id = d.name
            FROM domains d
            WHERE p.scope_type = 'domain'
              AND p.scope_id = d.id::text
              AND NOT EXISTS (
                  SELECT 1 FROM permissions dup
                  WHERE dup.role_id = p.role_id
                    AND dup.scope_type = 'domain'
                    AND dup.scope_id = d.name
                    AND dup.entity_type = p.entity_type
                    AND dup.operation = p.operation
              )
        """)
    )
    conn.execute(
        sa.text("""
            DELETE FROM permissions p
            USING domains d
            WHERE p.scope_type = 'domain'
              AND p.scope_id = d.id::text
        """)
    )


def _provision_domain_virtual_scopes() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            INSERT INTO virtual_scopes (scope_type, scope_id)
            SELECT 'domain', d.id FROM domains d
            ON CONFLICT (scope_type, scope_id) DO NOTHING
        """)
    )
    # Self entity-membership and self scope-binding (permission_cap NULL).
    conn.execute(
        sa.text("""
            INSERT INTO entity_memberships (virtual_scope_id, entity_type, entity_id)
            SELECT vs.id, 'domain', vs.scope_id
            FROM virtual_scopes vs
            WHERE vs.scope_type = 'domain'
            ON CONFLICT DO NOTHING
        """)
    )
    conn.execute(
        sa.text("""
            INSERT INTO scope_bindings (virtual_scope_id, scope_type, scope_id)
            SELECT vs.id, 'domain', vs.scope_id
            FROM virtual_scopes vs
            WHERE vs.scope_type = 'domain'
            ON CONFLICT DO NOTHING
        """)
    )
    # Bind each domain into its projects' virtual scopes so domain-scoped
    # permissions reach project entities (projects without a virtual scope
    # are skipped; they predate the virtual-scope chain).
    conn.execute(
        sa.text("""
            INSERT INTO scope_bindings (virtual_scope_id, scope_type, scope_id)
            SELECT vs.id, 'domain', d.id
            FROM groups g
            JOIN domains d ON g.domain_name = d.name
            JOIN virtual_scopes vs ON vs.scope_type = 'project' AND vs.scope_id = g.id
            ON CONFLICT DO NOTHING
        """)
    )
    # Users become entity members of their domain's virtual scope.
    conn.execute(
        sa.text("""
            INSERT INTO entity_memberships (virtual_scope_id, entity_type, entity_id)
            SELECT vs.id, 'user', u.uuid
            FROM users u
            JOIN domains d ON u.domain_name = d.name
            JOIN virtual_scopes vs ON vs.scope_type = 'domain' AND vs.scope_id = d.id
            ON CONFLICT DO NOTHING
        """)
    )


def _drop_domain_virtual_scopes() -> None:
    conn = op.get_bind()
    # Domain bindings inside project virtual scopes are not covered by the
    # cascade below, so drop them explicitly.
    conn.execute(
        sa.text("""
            DELETE FROM scope_bindings sb
            USING domains d
            WHERE sb.scope_type = 'domain'
              AND sb.scope_id = d.id
        """)
    )
    # FK ON DELETE CASCADE removes the self membership/binding edges.
    conn.execute(
        sa.text("""
            DELETE FROM virtual_scopes vs
            USING domains d
            WHERE vs.scope_type = 'domain'
              AND vs.scope_id = d.id
        """)
    )


def upgrade() -> None:
    _rekey_name_to_uuid()
    _provision_domain_virtual_scopes()


def downgrade() -> None:
    _drop_domain_virtual_scopes()
    _rekey_uuid_to_name()
