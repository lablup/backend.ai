"""Component tests for project unassign-users endpoint.

Tests: POST /v2/projects/{project_id}/users/unassign
"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.group.request import UnassignUsersFromProjectInput
from ai.backend.manager.models.group import association_groups_users


class TestUnassignUsersFromProject:
    """POST /v2/projects/{project_id}/users/unassign"""

    async def test_unassign_returns_unassigned_users(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        assigned_users: list[uuid.UUID],
        rbac_permission_fixture: uuid.UUID,
        db_engine: SAEngine,
    ) -> None:
        """Unassigning assigned users returns unassigned=True and user info."""
        result = await admin_v2_registry.project.unassign_users(
            group_fixture,
            UnassignUsersFromProjectInput(user_ids=assigned_users),
        )

        returned_ids = {u.id for u in result.items}
        assert returned_ids == set(assigned_users)

        # Verify rows removed from association_groups_users
        async with db_engine.begin() as conn:
            rows = (
                await conn.execute(
                    sa.select(association_groups_users.c.user_id).where(
                        (association_groups_users.c.group_id == str(group_fixture))
                        & (
                            association_groups_users.c.user_id.in_([
                                str(uid) for uid in assigned_users
                            ])
                        )
                    )
                )
            ).all()
            assert len(rows) == 0

    async def test_unassign_nonexistent_users_returns_empty(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        rbac_permission_fixture: uuid.UUID,
    ) -> None:
        """Unassigning user IDs not in the project returns unassigned=True with empty list."""
        fake_ids = [uuid.uuid4(), uuid.uuid4()]

        result = await admin_v2_registry.project.unassign_users(
            group_fixture,
            UnassignUsersFromProjectInput(user_ids=fake_ids),
        )

        assert result.items == []

    async def test_unassign_partial_users(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        assigned_users: list[uuid.UUID],
        rbac_permission_fixture: uuid.UUID,
        db_engine: SAEngine,
    ) -> None:
        """When only some user IDs are assigned, only those are returned."""
        fake_id = uuid.uuid4()
        mixed_ids = [assigned_users[0], fake_id]

        result = await admin_v2_registry.project.unassign_users(
            group_fixture,
            UnassignUsersFromProjectInput(user_ids=mixed_ids),
        )

        returned_ids = {u.id for u in result.items}
        assert returned_ids == {assigned_users[0]}

        # The other assigned users should still be in the association
        async with db_engine.begin() as conn:
            remaining = (
                await conn.execute(
                    sa.select(association_groups_users.c.user_id).where(
                        (association_groups_users.c.group_id == str(group_fixture))
                        & (
                            association_groups_users.c.user_id.in_([
                                str(uid) for uid in assigned_users[1:]
                            ])
                        )
                    )
                )
            ).all()
            assert len(remaining) == len(assigned_users) - 1
