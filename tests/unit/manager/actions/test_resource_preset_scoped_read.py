"""A regular user reads the presets of a resource group their domain is linked to.

``list_presets`` used to be wired public, so any authenticated caller read the presets
of any resource group they named. It is now checked at the scope the caller names: the
`public` singleton for the presets bound to no group, and the resource group itself for
the ones bound to it. What makes a linked group readable is the relation between the
domain and the group -- it makes the domain govern the group under a READ cap -- and the
``resource_preset`` READ the ``domain_member`` role holds in that domain.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.resource_group import ResourceGroupEntityType, ResourceGroupID
from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.global_scope.validator.refusing import (
    RefusingGlobalActionValidator,
)
from ai.backend.manager.actions.v2.scope.validator.rbac import (
    VirtualEntityScopeActionRBACValidator,
)
from ai.backend.manager.actions.v2.validators import ActionValidators
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.errors.permission import NotEnoughPermission
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import (
    DeploymentAutoScalingPolicyRow,
)
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.deployment_revision_preset import DeploymentRevisionPresetRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_group import ResourceGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_preset.scopes import (
    ResourceGroupResourcePresetTarget,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderRow
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.entity_membership_cap import (
    EntityMembershipCapRow,
)
from ai.backend.manager.models.virtual_entity.entity_membership_field import (
    EntityMembershipFieldRow,
)
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.ops.repository import OpsRepository
from ai.backend.manager.repositories.ops.v2.permission.provider import PermissionOpsProvider
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.resource_preset.actions.list_presets import (
    ListResourcePresetsAction,
    ListResourcePresetsResult,
)
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.testutils.db import TableOrORM, with_tables
from ai.backend.testutils.virtual_entity import VirtualEntitySeeder

# Row imports above ensure mapper initialization (FK dependency order).
_WITH_TABLES: list[TableOrORM] = [
    DomainRow,
    ResourceGroupRow,
    UserResourcePolicyRow,
    ProjectResourcePolicyRow,
    KeyPairResourcePolicyRow,
    RoleRow,
    UserRoleRow,
    UserRow,
    KeyPairRow,
    ProjectRow,
    ContainerRegistryRow,
    ImageRow,
    VFolderRow,
    EndpointRow,
    DeploymentPolicyRow,
    DeploymentAutoScalingPolicyRow,
    RuntimeVariantRow,
    DeploymentRevisionPresetRow,
    DeploymentRevisionRow,
    SessionRow,
    AgentRow,
    KernelRow,
    ReplicaGroupRow,
    RoutingRow,
    ResourcePresetRow,
    PermissionRow,
    VirtualEntityRow,
    ScopeBindingRow,
    EntityLabelRow,
    EntityMembershipRow,
    EntityMembershipCapRow,
    EntityMembershipFieldRow,
]


class _Graph:
    """The two resource groups the read may name, and the user in the linked one's domain."""

    linked: ResourceGroupID
    unlinked: ResourceGroupID
    domain: DomainID
    user_id: UserID

    def __init__(
        self,
        linked: ResourceGroupID,
        unlinked: ResourceGroupID,
        domain: DomainID,
        user_id: UserID,
    ) -> None:
        self.linked = linked
        self.unlinked = unlinked
        self.domain = domain
        self.user_id = user_id


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _WITH_TABLES):
        yield database_connection


@pytest.fixture
async def graph(db: ExtendedAsyncSAEngine) -> _Graph:
    seeder = VirtualEntitySeeder()
    domain = DomainID(uuid.uuid4())
    linked = ResourceGroupID(uuid.uuid4())
    unlinked = ResourceGroupID(uuid.uuid4())
    user_id = UserID(uuid.uuid4())
    domain_name = f"domain-{domain.hex[:8]}"

    async with db.begin_session() as sess:
        sess.add(DomainRow(id=domain, name=domain_name, total_resource_slots=ResourceSlot()))
        policy_name = f"policy-{uuid.uuid4().hex[:8]}"
        sess.add(
            UserResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=0,
                max_quota_scope_size=-1,
                max_session_count_per_model_session=0,
                max_customized_image_count=0,
            )
        )
        await sess.flush()
        sess.add(
            UserRow(
                uuid=user_id,
                username=f"user-{user_id.hex[:8]}",
                email=f"user-{user_id.hex[:8]}@test.com",
                resource_policy=policy_name,
                status=UserStatus.ACTIVE,
                need_password_change=False,
                sudo_session_enabled=False,
                domain_name=domain_name,
                domain_id=domain,
                role=UserRole.USER,
            )
        )
        await sess.flush()

        domain_node = await seeder.provision(sess, DomainEntityType(), domain)
        linked_node = await seeder.provision(sess, ResourceGroupEntityType(), linked)
        await seeder.provision(sess, ResourceGroupEntityType(), unlinked)
        await seeder.provision(sess, UserEntityType(), user_id)

        # What linking a domain and a resource group writes: the domain governs the
        # group under a READ cap.
        sess.add(
            ScopeBindingRow(
                virtual_entity_id=linked_node,
                scope_entity_id=domain_node,
                permission_cap=Permission.READ,
            )
        )

        # The role the domain_member preset instantiates in a domain.
        role = RoleRow(
            name=f"domain_member-{domain.hex[:8]}",
            status=RoleStatus.ACTIVE,
            scope_type=DomainEntityType(),
            scope_id=domain,
        )
        sess.add(role)
        await sess.flush()
        sess.add(
            PermissionRow(
                role_id=role.id,
                entity_type=ResourcePresetEntityType(),
                permission=Permission.READ,
            )
        )
        sess.add(UserRoleRow(user_id=user_id, role_id=role.id))
        await sess.commit()

    return _Graph(linked, unlinked, domain, user_id)


@pytest.fixture
def processors(db: ExtendedAsyncSAEngine) -> ResourcePresetProcessors:
    """The production wiring, with the RBAC validator reading this database and the
    service stubbed: what is under test is the gate, not the listing."""
    config_provider = MagicMock()
    config_provider.config.manager.rbac.enforcement_enabled = True
    check = RbacPermissionCheckRepository(PermissionOpsProvider(db), config_provider)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(
                scope=[VirtualEntityScopeActionRBACValidator(check, config_provider)],
                global_scope=[RefusingGlobalActionValidator()],
            ),
            repository=OpsRepository(V2DBOpsProvider(db)),
        )
    )
    service = MagicMock()
    service.list_presets = AsyncMock(return_value=ListResourcePresetsResult(presets=[]))
    return ResourcePresetProcessors(registry.group(GroupMeta(ResourcePresetEntityType())), service)


def _member(graph: _Graph) -> UserData:
    return UserData(
        user_id=graph.user_id,
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="domain",
        domain_id=graph.domain,
    )


def _action(group: ResourceGroupID) -> ListResourcePresetsAction:
    """The resource group alone: what the `public` half of the read needs is the
    `public_member` role, which is not what this test is about."""
    return ListResourcePresetsAction(
        targets=[ResourceGroupResourcePresetTarget(resource_group_id=group)],
        access_key="AKIATEST",
        resource_group=None,
    )


async def test_a_member_reads_the_presets_of_a_linked_resource_group(
    processors: ResourcePresetProcessors,
    graph: _Graph,
) -> None:
    with with_user(_member(graph)):
        result = await processors.list_presets.run(_action(graph.linked))

    assert result.presets == []


async def test_a_member_is_refused_a_resource_group_their_domain_is_not_linked_to(
    processors: ResourcePresetProcessors,
    graph: _Graph,
) -> None:
    with with_user(_member(graph)), pytest.raises(NotEnoughPermission):
        await processors.list_presets.run(_action(graph.unlinked))
