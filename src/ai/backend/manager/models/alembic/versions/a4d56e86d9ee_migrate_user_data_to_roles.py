"""migrate user data to roles

Revision ID: a4d56e86d9ee
Revises: 42feff246198
Create Date: 2025-08-06 21:28:29.354670

"""

import enum

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.engine import Connection, Row

from ai.backend.manager.models.base import GUID, EnumValueType, IDColumn
from ai.backend.manager.models.rbac_models.migration.enums import RoleSource
from ai.backend.manager.models.rbac_models.migration.models import (
    get_association_scopes_entities_table,
    get_object_permissions_table,
    get_roles_table,
    get_scope_permissions_table,
    get_user_roles_table,
    mapper_registry,
)
from ai.backend.manager.models.rbac_models.migration.types import (
    PermissionCreateInputGroup,
)
from ai.backend.manager.models.rbac_models.migration.user import (
    ProjectData,
    ProjectUserAssociationData,
    UserData,
    create_project_admin_role_and_permissions,
    create_project_member_role_and_permissions,
    create_user_self_role_and_permissions,
    map_user_to_project_role,
)
from ai.backend.manager.models.rbac_models.migration.utils import insert_from_create_input_group

# revision identifiers, used by Alembic.
revision = "a4d56e86d9ee"
down_revision = "42feff246198"
branch_labels = None
depends_on = None


class UserRole(enum.StrEnum):
    """
    User's role.
    """

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"
    MONITOR = "monitor"


def _get_groups_table() -> sa.Table:
    groups_table = sa.Table(
        "groups",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        extend_existing=True,
    )
    return groups_table


def _get_association_groups_users_table() -> sa.Table:
    association_groups_users_table = sa.Table(
        "association_groups_users",
        mapper_registry.metadata,
        IDColumn(),
        sa.Column("user_id", GUID, nullable=False),
        sa.Column(
            "group_id",
            GUID,
            sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        extend_existing=True,
    )
    return association_groups_users_table


def _get_users_table() -> sa.Table:
    users_table = sa.Table(
        "users",
        mapper_registry.metadata,
        IDColumn("uuid"),
        sa.Column("username", sa.String(length=64), unique=True),
        sa.Column("domain_name", sa.String(length=64), index=True),
        sa.Column("role", EnumValueType(UserRole), default=UserRole.USER),
        extend_existing=True,
    )
    return users_table


def _query_user_row(db_conn: Connection, offset: int, page_size: int) -> list[Row]:
    """
    Query all user rows with pagination.
    """
    users_table = _get_users_table()
    user_query = (
        sa.select(
            users_table.c.uuid,
            users_table.c.username,
            users_table.c.domain_name,
            users_table.c.role,
        )
        .offset(offset)
        .limit(page_size)
        .order_by(users_table.c.uuid)
    )
    return db_conn.execute(user_query).all()


def _create_user_self_roles_and_permissions(db_conn: Connection) -> None:
    """
    Migrate user data to roles and permissions.
    All users have a default self role and permissions.
    """
    offset = 0
    page_size = 1000
    while True:
        rows = _query_user_row(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = UserData.from_row(row)
            input_data = create_user_self_role_and_permissions(data)
            input_group.merge(input_data)
        insert_from_create_input_group(db_conn, input_group)


def _query_project_row(db_conn: Connection, offset: int, page_size: int) -> list[Row]:
    """
    Query all project rows with pagination.
    """
    groups_table = _get_groups_table()
    project_query = (
        sa.select(groups_table.c.id).offset(offset).limit(page_size).order_by(groups_table.c.id)
    )
    return db_conn.execute(project_query).all()


def _create_project_roles_and_permissions(db_conn: Connection) -> None:
    """
    Migrate project data to roles and permissions.
    All projects have a default admin role and a user role.
    """
    offset = 0
    page_size = 1000
    while True:
        rows = _query_project_row(db_conn, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = ProjectData.from_row(row)
            admin_input_data = create_project_admin_role_and_permissions(data)
            user_input_data = create_project_member_role_and_permissions(data)
            input_group.merge(admin_input_data)
            input_group.merge(user_input_data)
        insert_from_create_input_group(db_conn, input_group)


def _define_cte() -> sa.sql.Select:
    """
    Define a CTE to get all roles that need vfolder permissions.
    Join roles with scope permissions to get the first scope permissions row for each role.
    Assumes that all `scope_id`s of scope permissions in one role are the same.
    """
    roles_table = get_roles_table()
    scope_permissions_table = get_scope_permissions_table()
    association_groups_users_table = _get_association_groups_users_table()
    users_table = _get_users_table()

    roles_batch = (
        sa.select(
            roles_table.c.id.label("role_id"),
            roles_table.c.source,
            scope_permissions_table.c.scope_id,
            scope_permissions_table.c.scope_type,
            users_table.c.uuid.label("user_id"),
            users_table.c.role.label("user_role"),
        )
        .distinct(users_table.c.uuid, scope_permissions_table.c.scope_id)
        .select_from(
            sa.join(
                roles_table,
                scope_permissions_table,
                roles_table.c.id == scope_permissions_table.c.role_id,
            )
            .join(
                association_groups_users_table,
                sa.cast(scope_permissions_table.c.scope_id, UUID)
                == association_groups_users_table.c.group_id,
            )
            .join(users_table, association_groups_users_table.c.user_id == users_table.c.uuid)
        )
        .cte("roles_batch")
    )

    return roles_batch


def _query_admin_user_rows_with_project_role(
    db_conn: Connection, cte: sa.sql.Select, offset: int, page_size: int
) -> list[Row]:
    stmt = (
        sa.select(cte)
        .where(
            sa.and_(
                cte.c.user_role.in_([UserRole.ADMIN, UserRole.SUPERADMIN]),
                cte.c.source == RoleSource.SYSTEM,
            )
        )
        .offset(offset)
        .limit(page_size)
        .order_by(cte.c.role_id)
    )

    return db_conn.execute(stmt).all()


def _query_member_user_rows_with_project_role(
    db_conn: Connection, cte: sa.sql.Select, offset: int, page_size: int
) -> list[Row]:
    stmt = (
        sa.select(cte)
        .where(
            sa.and_(
                cte.c.user_role.not_in([UserRole.ADMIN, UserRole.SUPERADMIN]),
                cte.c.source == RoleSource.CUSTOM,
            )
        )
        .offset(offset)
        .limit(page_size)
        .order_by(cte.c.role_id)
    )

    return db_conn.execute(stmt).all()


def _map_admin_users_to_project_role(db_conn: Connection, roles_batch_cte: sa.sql.Select) -> None:
    offset = 0
    page_size = 1000

    while True:
        rows = _query_admin_user_rows_with_project_role(db_conn, roles_batch_cte, offset, page_size)
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = ProjectUserAssociationData(project_id=row.scope_id, user_id=row.user_id)
            input_data = map_user_to_project_role(row.role_id, data)
            input_group.merge(input_data)
        insert_from_create_input_group(db_conn, input_group)


def _map_member_users_to_project_role(db_conn: Connection, roles_batch_cte: sa.sql.Select) -> None:
    offset = 0
    page_size = 1000

    while True:
        rows = _query_member_user_rows_with_project_role(
            db_conn, roles_batch_cte, offset, page_size
        )
        offset += page_size
        if not rows:
            break
        input_group = PermissionCreateInputGroup()
        for row in rows:
            data = ProjectUserAssociationData(project_id=row.scope_id, user_id=row.user_id)
            input_data = map_user_to_project_role(row.role_id, data)
            input_group.merge(input_data)
        insert_from_create_input_group(db_conn, input_group)


def _map_users_to_project_role(db_conn: Connection) -> None:
    roles_batch_cte = _define_cte()
    _map_admin_users_to_project_role(db_conn, roles_batch_cte)
    _map_member_users_to_project_role(db_conn, roles_batch_cte)


def upgrade() -> None:
    conn = op.get_bind()
    _create_user_self_roles_and_permissions(conn)
    _create_project_roles_and_permissions(conn)
    _map_users_to_project_role(conn)


def downgrade() -> None:
    conn = op.get_bind()
    # Remove all data from the new RBAC tables
    conn.execute(sa.delete(get_association_scopes_entities_table()))
    conn.execute(sa.delete(get_object_permissions_table()))
    conn.execute(sa.delete(get_scope_permissions_table()))
    conn.execute(sa.delete(get_user_roles_table()))
    conn.execute(sa.delete(get_roles_table()))
