"""Component tests for project purge endpoint.

Tests: POST /v2/projects/purge
"""

from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.common.dto.manager.v2.group.request import PurgeProjectInput
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    Permission,
    ScopeType,
)
from ai.backend.manager.models.project.row import ProjectRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.testutils.fixtures import DomainFixtureData


@pytest.fixture()
async def project_with_rbac_rows(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
) -> AsyncIterator[tuple[uuid.UUID, str]]:
    """Insert a project along with the RBAC rows that the create flow would
    normally generate (two SYSTEM roles at the project's scope, scope-entity
    associations binding them, and scope-bound permissions). The test then
    exercises purge against this fully-controlled state.
    """
    project_id = uuid.uuid4()
    scope_id = str(project_id)
    admin_role_id = uuid.uuid4()
    member_role_id = uuid.uuid4()
    unique = secrets.token_hex(4)

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ProjectRow.__table__).values(
                id=project_id,
                name=f"rbac-purge-{unique}",
                description="Test project for RBAC purge cleanup",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
        virtual_entity_id = uuid.uuid4()
        await conn.execute(
            sa.insert(VirtualEntityRow.__table__).values(
                id=virtual_entity_id,
                entity_type=ScopeType.PROJECT,
                entity_id=project_id,
            )
        )
        await conn.execute(
            sa.insert(EntityMembershipRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                member_entity_id=virtual_entity_id,
                capped=False,
            )
        )
        await conn.execute(
            sa.insert(ScopeBindingRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                scope_entity_id=virtual_entity_id,
                permission_cap=None,
            )
        )
        await conn.execute(
            sa.insert(RoleRow.__table__).values([
                {
                    "id": admin_role_id,
                    "name": f"project-{scope_id[:8]}-admin",
                    "status": RoleStatus.ACTIVE,
                    "scope_type": ScopeType.PROJECT.value,
                    "scope_id": project_id,
                },
                {
                    "id": member_role_id,
                    "name": f"project-{scope_id[:8]}-member",
                    "status": RoleStatus.ACTIVE,
                    "scope_type": ScopeType.PROJECT.value,
                    "scope_id": project_id,
                },
            ])
        )
        # Both per-project SYSTEM roles are registered in the project's own scope.
        await conn.execute(
            sa.insert(PermissionRow.__table__).values([
                {
                    "role_id": admin_role_id,
                    "entity_type": EntityType.PROJECT,
                    "permission": Permission.UPDATE,
                },
                {
                    "role_id": member_role_id,
                    "entity_type": EntityType.PROJECT,
                    "permission": Permission.READ,
                },
            ])
        )

    yield project_id, scope_id

    async with db_engine.begin() as conn:
        # Permissions cascade-delete with the role; explicit delete is a safety net.
        await conn.execute(
            PermissionRow.__table__.delete().where(
                PermissionRow.__table__.c.role_id.in_([admin_role_id, member_role_id])
            )
        )
        await conn.execute(
            RoleRow.__table__.delete().where(
                RoleRow.__table__.c.id.in_([admin_role_id, member_role_id])
            )
        )
        await conn.execute(
            VirtualEntityRow.__table__.delete().where(
                VirtualEntityRow.__table__.c.entity_type == ScopeType.PROJECT,
                VirtualEntityRow.__table__.c.entity_id == project_id,
            )
        )
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id == project_id)
        )


class TestProjectPurgeRBACCleanup:
    async def test_admin_purge_cleans_up_rbac_rows(
        self,
        admin_v2_registry: V2ClientRegistry,
        project_with_rbac_rows: tuple[uuid.UUID, str],
        db_engine: SAEngine,
    ) -> None:
        """Purge must remove scope-entity associations and scope-bound permissions
        for the project, so the per-project SYSTEM roles do not end up with
        dangling scope references that resolve to NULL via GraphQL.
        """
        project_id, scope_id = project_with_rbac_rows

        await admin_v2_registry.project.admin_purge(PurgeProjectInput(group_id=project_id))

        async with db_engine.connect() as conn:
            group_row = await conn.scalar(
                sa.select(sa.func.count())
                .select_from(ProjectRow)
                .where(ProjectRow.id == project_id)
            )
            permissions_after = await conn.scalar(
                sa.select(sa.func.count())
                .select_from(PermissionRow)
                .join(RoleRow, RoleRow.id == PermissionRow.role_id)
                .where(
                    RoleRow.scope_type == RBACElementType.PROJECT,
                    RoleRow.scope_id == project_id,
                )
            )
        assert group_row == 0, "Group row should be removed after purge"
        assert permissions_after == 0, "the roles permissions should be gone after purge"
