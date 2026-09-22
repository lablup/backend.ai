"""Session component fixtures with the RBAC gate enforced against the real DB."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import ProcessorDependencies
from ai.backend.manager.actions.v2.bulk.validator.rbac import (
    VirtualEntityAtomicBulkActionRBACValidator,
    VirtualEntityPartialBulkActionRBACValidator,
)
from ai.backend.manager.actions.v2.global_scope.validator.rbac import (
    VirtualEntityGlobalActionRBACValidator,
)
from ai.backend.manager.actions.v2.membership.validator.rbac import (
    VirtualEntityMembershipActionRBACValidator,
)
from ai.backend.manager.actions.v2.relation.validator.rbac import (
    VirtualEntityRelationActionRBACValidator,
)
from ai.backend.manager.actions.v2.scope.validator.rbac import (
    VirtualEntityScopeActionRBACValidator,
)
from ai.backend.manager.actions.v2.single_entity.validator.rbac import (
    VirtualEntitySingleEntityActionRBACValidator,
)
from ai.backend.manager.actions.validators.rbac import VirtualEntityRBACValidators
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData
    from tests.component.session.conftest import SessionSeedData


@pytest.fixture()
def processor_registry(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> ProcessorRegistry[Any]:
    """The registry the session processors are built from, with the real RBAC validators."""
    permission_repo = RbacPermissionCheckRepository(
        PermissionOpsProvider(database_engine), config_provider
    )
    validators = VirtualEntityRBACValidators(
        scope=VirtualEntityScopeActionRBACValidator(permission_repo, config_provider),
        single_entity=VirtualEntitySingleEntityActionRBACValidator(
            permission_repo, config_provider
        ),
        partial_bulk=VirtualEntityPartialBulkActionRBACValidator(permission_repo),
        atomic_bulk=VirtualEntityAtomicBulkActionRBACValidator(permission_repo),
        relation=VirtualEntityRelationActionRBACValidator(permission_repo, config_provider),
        membership=VirtualEntityMembershipActionRBACValidator(permission_repo, config_provider),
        global_scope=VirtualEntityGlobalActionRBACValidator(permission_repo, config_provider),
    )
    return ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=validators.to_action_validators(),
            repository=OpsRepository(V2DBOpsProvider(database_engine)),
        )
    )


@pytest.fixture()
async def session_in_project(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
    session_seed: SessionSeedData,
) -> AsyncIterator[SessionSeedData]:
    """The admin's session with the graph rows creating it in the project writes: the
    project owns and governs it."""
    virtual_entities = VirtualEntityRow.__table__
    session_node = uuid.uuid4()
    async with db_engine.begin() as conn:
        project_node = (
            await conn.execute(
                sa.select(virtual_entities.c.id).where(
                    virtual_entities.c.entity_type == ProjectEntityType(),
                    virtual_entities.c.entity_id == group_fixture,
                )
            )
        ).scalar_one()
        await conn.execute(
            sa.insert(virtual_entities).values(
                id=session_node,
                entity_type=SessionEntityType(),
                entity_id=session_seed.session_id,
            )
        )
        await conn.execute(
            sa.insert(EntityMembershipRow.__table__).values([
                {
                    "virtual_entity_id": session_node,
                    "member_entity_id": session_node,
                    "capped": False,
                },
                {
                    "virtual_entity_id": project_node,
                    "member_entity_id": session_node,
                    "capped": False,
                },
            ])
        )
        await conn.execute(
            sa.insert(ScopeBindingRow.__table__).values([
                {
                    "virtual_entity_id": session_node,
                    "scope_entity_id": session_node,
                    "permission_cap": None,
                },
                {
                    "virtual_entity_id": session_node,
                    "scope_entity_id": project_node,
                    "permission_cap": None,
                },
            ])
        )
    yield session_seed
    async with db_engine.begin() as conn:
        # The membership and binding rows cascade from the virtual entity.
        await conn.execute(virtual_entities.delete().where(virtual_entities.c.id == session_node))


@pytest.fixture()
async def project_session_manager(
    database_engine: ExtendedAsyncSAEngine,
    regular_user_fixture: UserFixtureData,
    group_fixture: uuid.UUID,
) -> AsyncIterator[UserFixtureData]:
    """The regular user granted every operation on sessions within the project."""
    role_id = uuid.uuid4()
    async with database_engine.begin_session() as db_sess:
        db_sess.add(
            RoleRow(
                id=role_id,
                name=f"session-manager-{role_id.hex[:8]}",
                description="session component test role",
                scope_type=ProjectEntityType(),
                scope_id=group_fixture,
            )
        )
        await db_sess.flush()
        db_sess.add(UserRoleRow(user_id=regular_user_fixture.user_uuid, role_id=role_id))
        for operation in (
            Permission.READ,
            Permission.UPDATE,
            Permission.SOFT_DELETE,
            Permission.HARD_DELETE,
        ):
            db_sess.add(
                PermissionRow(
                    role_id=role_id,
                    entity_type=SessionEntityType(),
                    permission=operation,
                )
            )
        await db_sess.flush()
    yield regular_user_fixture
    async with database_engine.begin() as conn:
        await conn.execute(
            PermissionRow.__table__.delete().where(PermissionRow.__table__.c.role_id == role_id)
        )
        await conn.execute(
            UserRoleRow.__table__.delete().where(UserRoleRow.__table__.c.role_id == role_id)
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id == role_id))
