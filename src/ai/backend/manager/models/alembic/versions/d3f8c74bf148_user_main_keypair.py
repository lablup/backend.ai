"""user_main_keypair

Revision ID: d3f8c74bf148
Revises: 308bcecec5c2
Create Date: 2023-12-06 12:20:11.537908

"""

import enum
from typing import Any

import sqlalchemy as sa
from alembic import op
from sqlalchemy.orm import registry, relationship, selectinload, sessionmaker

from ai.backend.manager.defs import DEFAULT_KEYPAIR_RATE_LIMIT, DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME
from ai.backend.manager.models.base import GUID, EnumValueType, convention
from ai.backend.manager.models.keypair import generate_keypair, generate_ssh_keypair

# revision identifiers, used by Alembic.
revision = "d3f8c74bf148"
down_revision = "308bcecec5c2"
branch_labels = None
depends_on = None


metadata = sa.MetaData(naming_convention=convention)
mapper_registry = registry(metadata=metadata)
Base = mapper_registry.generate_base()

PAGE_SIZE = 100


class UserRole(enum.StrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


MAXIMUM_DOTFILE_SIZE = 64 * 1024  # 61 KiB


def upgrade() -> None:
    op.add_column("users", sa.Column("main_access_key", sa.String(length=20), nullable=True))
    op.create_foreign_key(
        op.f("fk_users_main_access_key_keypairs"),
        "users",
        "keypairs",
        ["main_access_key"],
        ["access_key"],
    )

    # Update all user's main_access_key
    # The oldest keypair of a user will be main_access_key
    class KeyPairRow(Base):  # type: ignore[valid-type, misc]
        __tablename__ = "keypairs"
        __table_args__ = {"extend_existing": True}

        user_id = sa.Column("user_id", sa.String(length=256))
        access_key = sa.Column("access_key", sa.String(length=20), primary_key=True)
        secret_key = sa.Column("secret_key", sa.String(length=40))
        is_active = sa.Column("is_active", sa.Boolean, index=True)
        is_admin = sa.Column(
            "is_admin", sa.Boolean, index=True, default=False, server_default=sa.false()
        )
        created_at = sa.Column("created_at", sa.DateTime(timezone=True))
        rate_limit = sa.Column("rate_limit", sa.Integer)
        num_queries = sa.Column("num_queries", sa.Integer, server_default="0")
        ssh_public_key = sa.Column("ssh_public_key", sa.Text, nullable=True)
        ssh_private_key = sa.Column("ssh_private_key", sa.Text, nullable=True)
        resource_policy = sa.Column(
            "resource_policy",
            sa.String(length=256),
            sa.ForeignKey("keypair_resource_policies.name"),
            nullable=False,
        )
        dotfiles = sa.Column(
            "dotfiles", sa.LargeBinary(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=b"\x90"
        )
        bootstrap_script = sa.Column(
            "bootstrap_script", sa.String(length=MAXIMUM_DOTFILE_SIZE), nullable=False, default=""
        )
        user = sa.Column("user", GUID, sa.ForeignKey("users.uuid"))
        user_row = relationship("UserRow", back_populates="keypairs", foreign_keys=user)

    class UserRow(Base):  # type: ignore[valid-type, misc]
        __tablename__ = "users"
        __table_args__ = {"extend_existing": True}

        uuid = sa.Column("uuid", GUID, primary_key=True)
        role = sa.Column("role", EnumValueType(UserRole), default=UserRole.USER)
        email = sa.Column("email", sa.String(length=64))
        main_access_key = sa.Column(
            "main_access_key",
            sa.String(length=20),
            sa.ForeignKey("keypairs.access_key", ondelete="RESTRICT"),
            nullable=True,
        )
        keypairs = relationship(
            "KeyPairRow", back_populates="user_row", foreign_keys=KeyPairRow.user
        )
        main_keypair = relationship("KeyPairRow", foreign_keys=main_access_key)

    def pick_main_keypair(keypair_list: list[KeyPairRow]) -> KeyPairRow | None:
        try:
            return sorted(keypair_list, key=lambda k: k.created_at)[0]
        except IndexError:
            return None

    def prepare_keypair(
        user_email,
        user_id,
        user_role,
    ) -> dict[str, Any]:
        ak, sk = generate_keypair()
        pubkey, privkey = generate_ssh_keypair()
        return {
            "user_id": user_email,
            "user": user_id,
            "access_key": ak,
            "secret_key": sk,
            "is_active": True,
            "is_admin": user_role in (UserRole.SUPERADMIN, UserRole.ADMIN),
            "resource_policy": DEFAULT_KEYPAIR_RESOURCE_POLICY_NAME,
            "rate_limit": DEFAULT_KEYPAIR_RATE_LIMIT,
            "num_queries": 0,
            "ssh_public_key": pubkey,
            "ssh_private_key": privkey,
        }

    connection = op.get_bind()
    sess_factory = sessionmaker(connection)
    db_session = sess_factory()
    while True:
        user_id_kp_maps = []
        user_query = (
            sa.select(UserRow)
            .where(UserRow.main_access_key.is_(sa.null()))
            .limit(PAGE_SIZE)
            .options(selectinload(UserRow.keypairs))
        )
        user_rows: list[UserRow] = db_session.scalars(user_query).all()

        if not user_rows:
            break

        for row in user_rows:
            main_kp = pick_main_keypair(row.keypairs)
            if main_kp is None:
                # Create new keypair when the user has no keypair
                kp_data = prepare_keypair(row.email, row.uuid, row.role)
                db_session.execute(sa.insert(KeyPairRow).values(**kp_data))
                user_id_kp_maps.append({
                    "user_id": row.uuid,
                    "main_access_key": kp_data["access_key"],
                })
            else:
                user_id_kp_maps.append({"user_id": row.uuid, "main_access_key": main_kp.access_key})

        update_query = (
            sa.update(UserRow)
            .where(UserRow.uuid == sa.bindparam("user_id"))
            .values(main_access_key=sa.bindparam("main_access_key"))
        )
        db_session.execute(update_query, user_id_kp_maps)


def downgrade() -> None:
    op.drop_constraint(op.f("fk_users_main_access_key_keypairs"), "users", type_="foreignkey")
    op.drop_column("users", "main_access_key")
