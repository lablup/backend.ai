"""add user model

Revision ID: 819c2b3830a9
Revises: 8e660aa31fe3
Create Date: 2019-05-02 00:21:43.704843

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from ai.backend.manager.models import UserRole
from ai.backend.manager.models.base import (
    GUID,
    EnumValueType,
    ForeignKeyIDColumn,
    IDColumn,
    convention,
)
from ai.backend.manager.models.user import PasswordColumn

# from ai.backend.manager.models import keypairs, users, UserRole


# revision identifiers, used by Alembic.
revision = "819c2b3830a9"
down_revision = "8e660aa31fe3"
branch_labels = None
depends_on = None


userrole_choices = list(map(str, UserRole))
userrole = postgresql.ENUM(*userrole_choices, name="userrole")


def upgrade():
    metadata = sa.MetaData(naming_convention=convention)
    # partial table to be preserved and referred
    keypairs = sa.Table(
        "keypairs",
        metadata,
        sa.Column("user_id", sa.String(length=256), index=True),
        sa.Column("access_key", sa.String(length=20), primary_key=True),
        sa.Column("secret_key", sa.String(length=40)),
        sa.Column("is_active", sa.Boolean, index=True),
        sa.Column("is_admin", sa.Boolean, index=True),
        ForeignKeyIDColumn("user", "users.uuid", nullable=False),
    )
    # partial table to insert the migrated data
    users = sa.Table(
        "users",
        metadata,
        IDColumn("uuid"),
        sa.Column("username", sa.String(length=64), unique=True),
        sa.Column("email", sa.String(length=64), index=True, nullable=False, unique=True),
        sa.Column("password", PasswordColumn()),
        sa.Column("need_password_change", sa.Boolean),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("role", EnumValueType(UserRole), default=UserRole.USER),
    )

    userrole.create(op.get_bind())
    op.create_table(
        "users",
        sa.Column("uuid", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=True),
        sa.Column("email", sa.String(length=64), nullable=False),
        sa.Column("password", PasswordColumn(), nullable=True),
        sa.Column("need_password_change", sa.Boolean(), nullable=True),
        sa.Column("first_name", sa.String(length=32), nullable=True),
        sa.Column("last_name", sa.String(length=32), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
        sa.Column(
            "role",
            postgresql.ENUM(*userrole_choices, name="userrole", create_type=False),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_users")),
        sa.UniqueConstraint("username", name=op.f("uq_users_username")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.add_column("keypairs", sa.Column("user", GUID(), nullable=True))
    op.create_foreign_key(op.f("fk_keypairs_user_users"), "keypairs", "users", ["user"], ["uuid"])

    # ### Create users based on keypair.user_id & associate keypairs.user to user record ###
    # Get all keypairs
    connection = op.get_bind()
    query = sa.select([
        keypairs.c.user_id,
        keypairs.c.access_key,
        keypairs.c.secret_key,
        keypairs.c.is_admin,
    ]).select_from(keypairs)
    results = connection.execute(query).fetchall()
    for keypair in results:
        email = keypair["user_id"]
        access_key = keypair["access_key"]
        is_admin = keypair["is_admin"]
        if email in [None, ""]:
            continue
        # Try to get a user whose email matches with current keypair's email
        query = (
            sa.select([users.c.uuid, users.c.role]).select_from(users).where(users.c.email == email)
        )
        user = connection.execute(query).first()
        if user:
            # Update user's role if current keypair is admin keypair
            user_uuid = user["uuid"]
            role = UserRole.ADMIN if is_admin else UserRole.USER
            if role == UserRole.ADMIN and user["role"] != UserRole.ADMIN:
                query = sa.update(users).values(role=UserRole.ADMIN).where(users.c.email == email)
                connection.execute(query)
        else:
            # Create new user (set username with email)
            role = UserRole.ADMIN if is_admin else UserRole.USER
            temp_password = keypair["secret_key"][:8]
            query = (
                sa.insert(users)
                .returning(users.c.uuid)
                .values(
                    username=email,
                    email=email,
                    password=temp_password,
                    need_password_change=True,
                    is_active=True,
                    role=role,
                )
            )
            user = connection.execute(query).first()
            user_uuid = user[0]
        # Update current keypair's `user` field with associated user's uuid.
        query = (
            sa.update(keypairs).values(user=user_uuid).where(keypairs.c.access_key == access_key)
        )
        connection.execute(query)

    # Make keypairs.user column NOT NULL.
    op.alter_column("keypairs", column_name="user", nullable=False)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(op.f("fk_keypairs_user_users"), "keypairs", type_="foreignkey")
    op.drop_column("keypairs", "user")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    # ### end Alembic commands ###

    userrole.drop(op.get_bind())
