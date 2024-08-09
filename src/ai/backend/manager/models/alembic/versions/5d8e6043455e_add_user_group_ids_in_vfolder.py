"""add_user_group_ids_in_vfolder

Revision ID: 5d8e6043455e
Revises: 02950808ca3d
Create Date: 2019-06-06 15:02:58.804516

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql.expression import bindparam

from ai.backend.manager.models.base import GUID, ForeignKeyIDColumn, IDColumn, convention

# revision identifiers, used by Alembic.
revision = "5d8e6043455e"
down_revision = "02950808ca3d"
branch_labels = None
depends_on = None


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)
    # partial table to be preserved and referred
    keypairs = sa.Table(
        "keypairs",
        metadata,
        sa.Column("access_key", sa.String(length=20), primary_key=True),
        ForeignKeyIDColumn("user", "users.uuid", nullable=False),
    )
    vfolders = sa.Table(
        "vfolders",
        metadata,
        IDColumn("id"),
        sa.Column("belongs_to", sa.String(length=20), sa.ForeignKey("keypairs.access_key")),
        sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=True),
        sa.Column("group", GUID, sa.ForeignKey("groups.id"), nullable=True),
    )
    vfolder_permissions = sa.Table(
        "vfolder_permissions",
        metadata,
        sa.Column(
            "vfolder",
            GUID,
            sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("access_key", sa.String(length=20), sa.ForeignKey("keypairs.access_key")),
        sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=True),
    )

    op.add_column("vfolders", sa.Column("user", GUID(), nullable=True))
    op.add_column("vfolders", sa.Column("group", GUID(), nullable=True))
    op.create_foreign_key(op.f("fk_vfolders_user_users"), "vfolders", "users", ["user"], ["uuid"])
    op.create_foreign_key(op.f("fk_vfolders_group_groups"), "vfolders", "groups", ["group"], ["id"])
    op.add_column("vfolder_permissions", sa.Column("user", GUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_vfolder_permissions_user_users"),
        "vfolder_permissions",
        "users",
        ["user"],
        ["uuid"],
    )

    connection = op.get_bind()

    # Migrate vfolders' belongs_to keypair into user.
    j = vfolders.join(keypairs, vfolders.c.belongs_to == keypairs.c.access_key)
    query = sa.select([vfolders.c.id, keypairs.c.user]).select_from(j)
    results = connection.execute(query).fetchall()
    updates = [{"vid": row.id, "user": row.user} for row in results]
    if updates:
        query = (
            sa.update(vfolders)
            .values(user=bindparam("user"))
            .where(vfolders.c.id == bindparam("vid"))
        )
        connection.execute(query, updates)

    # Migrate vfolder_permissions' access_key into user.
    j = vfolder_permissions.join(
        keypairs, vfolder_permissions.c.access_key == keypairs.c.access_key
    )
    query = sa.select([
        vfolder_permissions.c.vfolder,
        keypairs.c.access_key,
        keypairs.c.user,
    ]).select_from(j)
    results = connection.execute(query).fetchall()
    updates = [
        {"_vfolder": row.vfolder, "_access_key": row.access_key, "_user": row.user}
        for row in results
    ]
    if updates:
        query = (
            sa.update(vfolder_permissions)
            .values(user=bindparam("_user"))
            .where(vfolder_permissions.c.vfolder == bindparam("_vfolder"))
            .where(vfolder_permissions.c.access_key == bindparam("_access_key"))
        )
        connection.execute(query, updates)

    op.drop_constraint("fk_vfolders_belongs_to_keypairs", "vfolders", type_="foreignkey")
    op.drop_column("vfolders", "belongs_to")
    op.alter_column("vfolder_permissions", "user", nullable=False)
    op.drop_constraint(
        "fk_vfolder_permissions_access_key_keypairs", "vfolder_permissions", type_="foreignkey"
    )
    op.drop_column("vfolder_permissions", "access_key")


def downgrade():
    #######################################################################
    # CAUTION: group vfolders will be lost by downgrading this migration!
    #######################################################################

    metadata = sa.MetaData(naming_convention=convention)
    # partial table to be preserved and referred
    keypairs = sa.Table(
        "keypairs",
        metadata,
        sa.Column("access_key", sa.String(length=20), primary_key=True),
        ForeignKeyIDColumn("user", "users.uuid", nullable=False),
    )
    vfolders = sa.Table(
        "vfolders",
        metadata,
        IDColumn("id"),
        sa.Column("belongs_to", sa.String(length=20), sa.ForeignKey("keypairs.access_key")),
        sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=True),
        # sa.Column('group', GUID, sa.ForeignKey('groups.id'), nullable=True),
    )
    vfolder_permissions = sa.Table(
        "vfolder_permissions",
        metadata,
        sa.Column(
            "vfolder",
            GUID,
            sa.ForeignKey("vfolders.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("access_key", sa.String(length=20), sa.ForeignKey("keypairs.access_key")),
        sa.Column("user", GUID, sa.ForeignKey("users.uuid"), nullable=True),
    )

    op.add_column(
        "vfolders",
        sa.Column("belongs_to", sa.String(length=20), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "fk_vfolders_belongs_to_keypairs", "vfolders", "keypairs", ["belongs_to"], ["access_key"]
    )
    op.add_column(
        "vfolder_permissions",
        sa.Column("access_key", sa.String(length=20), autoincrement=False, nullable=True),
    )
    op.create_foreign_key(
        "fk_vfolder_permissions_access_key_keypairs",
        "vfolder_permissions",
        "keypairs",
        ["access_key"],
        ["access_key"],
    )

    connection = op.get_bind()

    # Migrate vfolders' user_id into belongs_to.
    j = vfolders.join(keypairs, vfolders.c.user == keypairs.c.user)
    query = sa.select([vfolders.c.id, keypairs.c.access_key]).select_from(j)
    results = connection.execute(query).fetchall()
    updates = [{"vid": row.id, "belongs_to": row.access_key} for row in results]
    if updates:
        query = (
            sa.update(vfolders)
            .values(belongs_to=bindparam("belongs_to"))
            .where(vfolders.c.id == bindparam("vid"))
        )
        connection.execute(query, updates)

    # Migrate vfolder_permissions' used into access_key.
    j = vfolder_permissions.join(keypairs, vfolder_permissions.c.user == keypairs.c.user)
    query = sa.select([
        vfolder_permissions.c.vfolder,
        keypairs.c.user,
        keypairs.c.access_key,
    ]).select_from(j)
    results = connection.execute(query).fetchall()
    updates = [
        {"_vfolder": row.vfolder, "_access_key": row.access_key, "_user": row.user}
        for row in results
    ]
    if updates:
        query = (
            sa.update(vfolder_permissions)
            .values(access_key=bindparam("_access_key"))
            .where(vfolder_permissions.c.vfolder == bindparam("_vfolder"))
            .where(vfolder_permissions.c.user == bindparam("_user"))
        )
        connection.execute(query, updates)

    op.alter_column("vfolders", "belongs_to", nullable=False)
    op.alter_column("vfolder_permissions", "access_key", nullable=False)
    op.drop_constraint(op.f("fk_vfolders_user_users"), "vfolders", type_="foreignkey")
    op.drop_constraint(op.f("fk_vfolders_group_groups"), "vfolders", type_="foreignkey")
    op.drop_column("vfolders", "user")
    op.drop_column("vfolders", "group")
    op.drop_constraint(
        op.f("fk_vfolder_permissions_user_users"), "vfolder_permissions", type_="foreignkey"
    )
    op.drop_column("vfolder_permissions", "user")
