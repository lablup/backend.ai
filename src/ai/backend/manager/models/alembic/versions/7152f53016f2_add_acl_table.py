"""add_acl_table

Revision ID: 7152f53016f2
Revises: 213a04e90ecf
Create Date: 2022-12-23 14:00:36.983543

"""
from collections import defaultdict
from functools import reduce

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as psql

from ai.backend.common.types import ProjectPermission
from ai.backend.manager.models.acl import AccessControlLists, AccessibleItem
from ai.backend.manager.models.base import GUID
from ai.backend.manager.models.group import association_groups_users as agus
from ai.backend.manager.models.user import UserRole, users

# revision identifiers, used by Alembic.
revision = "7152f53016f2"
down_revision = "213a04e90ecf"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "access_control_lists",
        sa.Column("id", GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("subject_type", sa.String(), nullable=False),
        sa.Column("subject_id", GUID(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=False),
        sa.Column("target_id", GUID(), nullable=False),
        sa.Column("permission_type", sa.String(), nullable=False),
        sa.Column("allowed_actions", psql.ARRAY(sa.String()), nullable=True),
        sa.Column("blocked_actions", psql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_access_control_lists")),
    )
    op.create_index(
        op.f("ix_access_control_lists_subject_id"),
        "access_control_lists",
        ["subject_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_access_control_lists_target_id"),
        "access_control_lists",
        ["target_id"],
        unique=False,
    )
    connection = op.get_bind()
    j = sa.join(agus, users, agus.c.user_id == users.c.uuid)
    query = sa.select([agus, users.c.role]).select_from(j)
    results = connection.execute(query).fetchall()
    insert_data = [
        {
            "subject_type": AccessibleItem.USER,
            "subject_id": row["user_id"],
            "target_type": AccessibleItem.PROJECT,
            "target_id": row["group_id"],
            "permission_type": ProjectPermission,
            "allowed_actions": [ProjectPermission.ADMIN]
            if row["role"] in (UserRole.ADMIN, UserRole.SUPERADMIN)
            else [ProjectPermission.USE],
        }
        for row in results
    ]
    if insert_data:
        connection.execute(sa.insert(AccessControlLists), insert_data)


def downgrade():
    connection = op.get_bind()
    query = sa.select(AccessControlLists).where(
        (AccessControlLists.subject_type == AccessibleItem.USER)
        & (AccessControlLists.target_type == AccessibleItem.PROJECT)
        & (AccessControlLists.permission_type == ProjectPermission)
    )
    results = connection.execute(query).fetchall()
    insert_data = [
        {
            "user_id": row["subject_id"],
            "group_id": row["target_id"],
        }
        for row in results
        if ProjectPermission.ADMIN in row["allowed_actions"]
        or ProjectPermission.USE in row["allowed_actions"]
    ]
    if insert_data:

        def add_cond(merged_cond, cond):
            uid, gid = cond["user_id"], cond["group_id"]
            return merged_cond | ((agus.c.user_id == uid) & (agus.c.group_id == gid))

        init_data = (agus.c.user_id == insert_data[0]["user_id"]) & (
            agus.c.group_id == insert_data[0]["group_id"]
        )
        cond = reduce(add_cond, insert_data, init_data)
        query = sa.select([agus]).where(cond)
        results = connection.execute(query).fetchall()
        user_group_map = defaultdict(list)
        for row in results:
            user_group_map[row["user_id"]].append(row["group_id"])

        filtered_data = []
        for d in insert_data:
            if d["group_id"] not in user_group_map[d["user_id"]]:
                filtered_data.append(
                    {
                        "user_id": d["user_id"],
                        "group_id": d["group_id"],
                    }
                )
        if filtered_data:
            connection.execute(sa.insert(agus), filtered_data)

    op.drop_index(op.f("ix_access_control_lists_target_id"), table_name="access_control_lists")
    op.drop_index(op.f("ix_access_control_lists_subject_id"), table_name="access_control_lists")
    op.drop_table("access_control_lists")
