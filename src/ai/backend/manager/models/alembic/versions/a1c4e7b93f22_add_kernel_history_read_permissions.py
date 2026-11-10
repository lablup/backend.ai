"""add kernel history read permissions to roles that can read kernels

Intentionally a no-op. As shipped, this migration was inert: it mirrored READ
grants from a ``kernel`` entity that nothing creates — kernel-entity permission
records are deliberately kept empty — so its SELECT matched zero rows, which
also masked its INSERT omitting the NOT NULL ``permissions.permission`` column.
The body has been emptied to make the no-op explicit; the revision is kept only
because it has already been applied.

Kernel scheduling history is authorized through ``session`` READ via the RBAC
scope chain (kernel -> session -> user/project) instead, so no ``kernel:history``
grant is wanted. See ``SearchKernelScopedHistoryAction``.

Revision ID: a1c4e7b93f22
Revises: 3f9a1c7b2e04
Create Date: 2026-07-20 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = "a1c4e7b93f22"
down_revision = "3f9a1c7b2e04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
