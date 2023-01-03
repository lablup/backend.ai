"""add_project_admin_user_role

Revision ID: b43752739fbc
Revises: 213a04e90ecf
Create Date: 2022-12-29 12:38:50.250943

"""
import enum
import textwrap

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import text

from ai.backend.manager.models.base import metadata
from ai.backend.manager.models.user import UserRole, users

# revision identifiers, used by Alembic.
revision = "b43752739fbc"
down_revision = "213a04e90ecf"
branch_labels = None
depends_on = None

enum_name = UserRole.__name__.lower()


class LegacyUserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


role_values = set([role.value for role in UserRole])
legacy_role_values = set([role.value for role in LegacyUserRole])

new_names = role_values - legacy_role_values
legacy_names = legacy_role_values - role_values


def _delete_enum_value(connection, enum_name, val):
    connection.execute(
        text(
            textwrap.dedent(
                f"""DELETE FROM pg_enum
                    WHERE enumlabel = '{val}'
                    AND enumtypid = (
                    SELECT oid FROM pg_type WHERE typname = '{enum_name}'
                );"""
            )
        )
    )


def upgrade():
    """"""
    conn = op.get_bind()

    for n in new_names:
        conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE '{n}';"))
    conn.commit()

    # replace "admin" to "domain_admin"
    conn.execute(
        text(
            f"UPDATE users SET role = '{UserRole.DOMAIN_ADMIN.value}' WHERE role = '{LegacyUserRole.ADMIN.value}';"
        )
    )

    for n in legacy_names:
        _delete_enum_value(conn, enum_name, n)
    conn.commit()


def downgrade():
    """"""
    conn = op.get_bind()

    for n in legacy_names:
        conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE '{n}';"))
    conn.commit()

    # replace "domain_admin" to "admin"
    conn.execute(
        text(
            f"UPDATE users SET role = '{LegacyUserRole.ADMIN.value}' WHERE role = '{UserRole.DOMAIN_ADMIN.value}';"
        )
    )

    for n in new_names:
        _delete_enum_value(conn, enum_name, n)
    conn.commit()
