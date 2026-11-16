"""Resource policy fixtures with the RBAC gate enforced against the real DB.

What the declaration grants is the whole subject here, so the caller is a user created
the way every user is and holds nothing but the roles the seed presets call for.
"""

from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.resource_policy import (
    KeyPairResourcePolicyEntityType,
    ProjectResourcePolicyEntityType,
    UserResourcePolicyEntityType,
)
from ai.backend.common.data.entity.role import RoleEntityType
from ai.backend.common.data.entity.role_preset import RolePresetID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.types import AccessKey
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
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
from ai.backend.manager.api.adapters.resource_policy.adapter import ResourcePolicyAdapter
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.resource_policy.handler import V2ResourcePolicyHandler
from ai.backend.manager.api.rest.v2.resource_policy.registry import (
    register_v2_resource_policy_routes,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.auth.hash import PasswordHashAlgorithm
from ai.backend.manager.data.keypair.types import KeyPairSecrets
from ai.backend.manager.data.permission.seed.loader import RoleSeedLoader
from ai.backend.manager.models.hasher.types import PasswordInfo
from ai.backend.manager.models.keypair import keypairs
from ai.backend.manager.models.project import ProjectRow, association_groups_users
from ai.backend.manager.models.project.creators import ProjectCreator
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow
from ai.backend.manager.models.user import UserRole, UserStatus, users
from ai.backend.manager.models.user.creators import UserCreator
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.user.provider import UserOpsProvider
from ai.backend.manager.repositories.ops.v2.user.write import FullUserCreator
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.secret.types import SecretValue
from ai.backend.manager.services.keypair_resource_policy.processors import (
    KeypairResourcePolicyProcessors,
)
from ai.backend.manager.services.processors import Processors
from ai.backend.manager.services.project_resource_policy.processors import (
    ProjectResourcePolicyProcessors,
)
from ai.backend.manager.services.user_resource_policy.processors import (
    UserResourcePolicyProcessors,
)
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo

# The seed roles a user created the way every user is comes to hold: their own scope's,
# and the one every project puts on its roster.
_AUTO_ASSIGNED: tuple[str, ...] = ("user_owner", "project_member")

_BITS: tuple[Permission, ...] = (
    Permission.READ,
    Permission.UPDATE,
    Permission.CREATE,
    Permission.SOFT_DELETE,
    Permission.HARD_DELETE,
)


@dataclass(frozen=True)
class SeededCaller:
    """A user holding nothing but the seed roles, and the key they authorize with."""

    user_id: UserID
    access_key: str
    secret_key: str


@pytest.fixture()
def processor_registry(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
) -> ProcessorRegistry[Any]:
    """The registry the resource policy processors are built from, with the real RBAC
    validators."""
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
def server_module_registries(
    route_deps: RouteDeps,
    processor_registry: ProcessorRegistry[Any],
) -> list[RouteRegistry]:
    """The v2 resource policy routes, served by processors the RBAC gate runs on."""
    processors = MagicMock(spec=Processors)
    processors.keypair_resource_policy = KeypairResourcePolicyProcessors(
        group=processor_registry.group(GroupMeta(KeyPairResourcePolicyEntityType()))
    )
    processors.user_resource_policy = UserResourcePolicyProcessors(
        group=processor_registry.group(GroupMeta(UserResourcePolicyEntityType()))
    )
    processors.project_resource_policy = ProjectResourcePolicyProcessors(
        group=processor_registry.group(GroupMeta(ProjectResourcePolicyEntityType()))
    )
    handler = V2ResourcePolicyHandler(
        adapter=ResourcePolicyAdapter(
            processors.keypair_resource_policy,
            processors.user_resource_policy,
            processors.project_resource_policy,
        )
    )
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_resource_policy_routes(handler, route_deps))
    return [v2_reg]


@pytest.fixture()
async def declared_presets(db_engine: SAEngine) -> AsyncIterator[list[RolePresetID]]:
    """The auto-assigned presets and their grants as the seed declaration states them."""
    seeds = [seed for seed in RoleSeedLoader().load() if seed.name in _AUTO_ASSIGNED]
    assert len(seeds) == len(_AUTO_ASSIGNED)
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(RolePresetRow.__table__).values([
                {
                    "id": seed.id,
                    "name": seed.name,
                    "scope_type": str(seed.scope_type),
                    "auto_assign": seed.auto_assign,
                    "deleted": False,
                }
                for seed in seeds
            ])
        )
        await conn.execute(
            sa.insert(RolePermissionPresetRow.__table__).values([
                {"role_preset_id": seed.id, "entity_type": entity_type, "permission": bit}
                for seed in seeds
                for entity_type, granted in seed.permissions.items()
                for bit in _BITS
                if granted & bit
            ])
        )
    preset_ids = [seed.id for seed in seeds]
    yield preset_ids
    async with db_engine.begin() as conn:
        await conn.execute(
            RolePermissionPresetRow.__table__.delete().where(
                RolePermissionPresetRow.__table__.c.role_preset_id.in_(preset_ids)
            )
        )
        await conn.execute(
            RolePresetRow.__table__.delete().where(RolePresetRow.__table__.c.id.in_(preset_ids))
        )


@pytest.fixture()
async def seeded_project(
    database_engine: ExtendedAsyncSAEngine,
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
    declared_presets: list[RolePresetID],
) -> AsyncIterator[ProjectID]:
    """A project registered the way every project is, so it carries the roles its
    presets call for."""
    repository = ProjectRepository(
        database_engine,
        V2DBOpsProvider(database_engine),
        ResourcePolicyOpsProvider(database_engine),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    project = await repository.create_project(
        ProjectCreator(
            name=f"policy-project-{secrets.token_hex(4)}",
            domain_id=DomainID(domain_fixture.domain_id),
            domain_name=domain_fixture.domain_name,
            resource_policy=resource_policy_fixture,
        )
    )
    project_id = ProjectID(project.id)
    yield project_id
    async with db_engine.begin() as conn:
        role_ids = (
            (
                await conn.execute(
                    sa.select(RoleRow.__table__.c.id).where(
                        RoleRow.__table__.c.scope_type == ProjectEntityType(),
                        RoleRow.__table__.c.scope_id == project_id,
                    )
                )
            )
            .scalars()
            .all()
        )
        await conn.execute(
            VirtualEntityRow.__table__.delete().where(
                sa.or_(
                    sa.and_(
                        VirtualEntityRow.__table__.c.entity_type == RoleEntityType(),
                        VirtualEntityRow.__table__.c.entity_id.in_(role_ids),
                    ),
                    sa.and_(
                        VirtualEntityRow.__table__.c.entity_type == ProjectEntityType(),
                        VirtualEntityRow.__table__.c.entity_id == project_id,
                    ),
                )
            )
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id.in_(role_ids)))
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id == project_id)
        )


@pytest.fixture()
async def seeded_caller(
    database_engine: ExtendedAsyncSAEngine,
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    seeded_project: ProjectID,
    resource_policy_fixture: str,
    declared_presets: list[RolePresetID],
) -> AsyncIterator[SeededCaller]:
    """A regular user created the way every user is, put on the shared project."""
    unique = secrets.token_hex(4)
    access_key = f"AKTEST{secrets.token_hex(7).upper()}"
    secret_key = secrets.token_hex(20)
    provider = UserOpsProvider(database_engine)
    async with provider.write_ops() as w:
        result = await w.create_user(
            FullUserCreator(
                user=UserCreator(
                    email=f"policy-reader-{unique}@test.local",
                    username=f"policy-reader-{unique}",
                    password=PasswordInfo(
                        password=secrets.token_urlsafe(8),
                        algorithm=PasswordHashAlgorithm.PBKDF2_SHA256,
                        rounds=1_000,
                        salt_size=32,
                    ),
                    need_password_change=False,
                    domain_id=DomainID(domain_fixture.domain_id),
                    status=UserStatus.ACTIVE,
                    role=UserRole.USER,
                    resource_policy=resource_policy_fixture,
                ),
                keypair_secrets=KeyPairSecrets(
                    access_key=AccessKey(access_key),
                    secret_key=SecretValue(secret_key),
                    ssh_public_key="ssh-rsa test",
                    ssh_private_key="test-private-key",
                ),
                keypair_resource_policy=resource_policy_fixture,
            )
        )
        user_id = UserID(result.user.id)
        await w.join_projects(user_id, DomainID(domain_fixture.domain_id), [seeded_project])
    yield SeededCaller(user_id=user_id, access_key=access_key, secret_key=secret_key)
    async with db_engine.begin() as conn:
        personal_ids = (
            (
                await conn.execute(
                    sa.select(ProjectRow.__table__.c.id).where(
                        ProjectRow.__table__.c.creator_id == user_id
                    )
                )
            )
            .scalars()
            .all()
        )
        role_ids = (
            (
                await conn.execute(
                    sa.select(RoleRow.__table__.c.id).where(
                        RoleRow.__table__.c.scope_type == UserEntityType(),
                        RoleRow.__table__.c.scope_id == user_id,
                    )
                )
            )
            .scalars()
            .all()
        )
        await conn.execute(
            association_groups_users.delete().where(association_groups_users.c.user_id == user_id)
        )
        await conn.execute(keypairs.delete().where(keypairs.c.user == user_id))
        # Roles, their permissions and assignments, and every edge go with the nodes.
        await conn.execute(
            VirtualEntityRow.__table__.delete().where(
                sa.or_(
                    sa.and_(
                        VirtualEntityRow.__table__.c.entity_type == RoleEntityType(),
                        VirtualEntityRow.__table__.c.entity_id.in_(role_ids),
                    ),
                    sa.and_(
                        VirtualEntityRow.__table__.c.entity_type == ProjectEntityType(),
                        VirtualEntityRow.__table__.c.entity_id.in_(personal_ids),
                    ),
                    sa.and_(
                        VirtualEntityRow.__table__.c.entity_type == UserEntityType(),
                        VirtualEntityRow.__table__.c.entity_id == user_id,
                    ),
                )
            )
        )
        await conn.execute(RoleRow.__table__.delete().where(RoleRow.__table__.c.id.in_(role_ids)))
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id.in_(personal_ids))
        )
        await conn.execute(users.delete().where(users.c.uuid == user_id))


@pytest.fixture()
async def seeded_caller_registry(
    server: ServerInfo,
    seeded_caller: SeededCaller,
) -> AsyncIterator[V2ClientRegistry]:
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(access_key=seeded_caller.access_key, secret_key=seeded_caller.secret_key),
    )
    try:
        yield registry
    finally:
        await registry.close()
