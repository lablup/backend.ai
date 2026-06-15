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
from ai.backend.common.data.permission.types import RBACElementType, RelationType
from ai.backend.common.dto.manager.v2.group.request import PurgeProjectInput
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    Permission,
    ScopeType,
)
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
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
            sa.insert(GroupRow.__table__).values(
                id=project_id,
                name=f"rbac-purge-{unique}",
                description="Test project for RBAC purge cleanup",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
        await conn.execute(
            sa.insert(RoleRow.__table__).values([
                {
                    "id": admin_role_id,
                    "name": f"project-{scope_id[:8]}-admin",
                    "status": RoleStatus.ACTIVE,
                },
                {
                    "id": member_role_id,
                    "name": f"project-{scope_id[:8]}-member",
                    "status": RoleStatus.ACTIVE,
                },
            ])
        )
        # Both per-project SYSTEM roles are registered in the project's own scope.
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__).values([
                {
                    "scope_type": ScopeType.PROJECT,
                    "scope_id": scope_id,
                    "entity_type": EntityType.ROLE,
                    "entity_id": str(admin_role_id),
                    "relation_type": RelationType.AUTO,
                },
                {
                    "scope_type": ScopeType.PROJECT,
                    "scope_id": scope_id,
                    "entity_type": EntityType.ROLE,
                    "entity_id": str(member_role_id),
                    "relation_type": RelationType.AUTO,
                },
                # Project registered as an entity in the domain scope.
                {
                    "scope_type": ScopeType.DOMAIN,
                    "scope_id": domain_fixture.domain_name,
                    "entity_type": EntityType.PROJECT,
                    "entity_id": scope_id,
                    "relation_type": RelationType.AUTO,
                },
            ])
        )
        await conn.execute(
            sa.insert(PermissionRow.__table__).values([
                {
                    "role_id": admin_role_id,
                    "scope_type": ScopeType.PROJECT,
                    "scope_id": scope_id,
                    "entity_type": EntityType.PROJECT,
                    "operation": OperationType.UPDATE,
                    "permission": Permission.UPDATE,
                },
                {
                    "role_id": member_role_id,
                    "scope_type": ScopeType.PROJECT,
                    "scope_id": scope_id,
                    "entity_type": EntityType.PROJECT,
                    "operation": OperationType.READ,
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
            AssociationScopesEntitiesRow.__table__.delete().where(
                sa.or_(
                    AssociationScopesEntitiesRow.__table__.c.scope_id == scope_id,
                    AssociationScopesEntitiesRow.__table__.c.entity_id == scope_id,
                )
            )
        )
        await conn.execute(
            RoleRow.__table__.delete().where(
                RoleRow.__table__.c.id.in_([admin_role_id, member_role_id])
            )
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == project_id))


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
                sa.select(sa.func.count()).select_from(GroupRow).where(GroupRow.id == project_id)
            )
            ase_after = await conn.scalar(
                sa.select(sa.func.count())
                .select_from(AssociationScopesEntitiesRow)
                .where(
                    sa.or_(
                        sa.and_(
                            AssociationScopesEntitiesRow.scope_type == RBACElementType.PROJECT,
                            AssociationScopesEntitiesRow.scope_id == scope_id,
                        ),
                        sa.and_(
                            AssociationScopesEntitiesRow.entity_type == RBACElementType.PROJECT,
                            AssociationScopesEntitiesRow.entity_id == scope_id,
                        ),
                    )
                )
            )
            permissions_after = await conn.scalar(
                sa.select(sa.func.count())
                .select_from(PermissionRow)
                .where(
                    PermissionRow.scope_type == RBACElementType.PROJECT,
                    PermissionRow.scope_id == scope_id,
                )
            )
        assert group_row == 0, "Group row should be removed after purge"
        assert ase_after == 0, "association_scopes_entities rows should be cleaned up after purge"
        assert permissions_after == 0, "scope-bound permissions should be cleaned up after purge"
