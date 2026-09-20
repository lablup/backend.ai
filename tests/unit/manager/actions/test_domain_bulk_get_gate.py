"""A regular user reads the domain they belong to and no other.

``bulk_get`` of domain used to be wired public, so any authenticated caller read every
domain. It is now checked per domain, and what makes the caller's own domain readable
is the ``domain_member`` role placed in that domain: every node owns and governs
itself, so READ on the domain type held at domain X reaches domain X itself.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock

import pytest

from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta, ProcessorDependencies
from ai.backend.manager.actions.v2.bulk.validator.rbac import (
    VirtualEntityPartialBulkActionRBACValidator,
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
from ai.backend.manager.services.domain.actions.bulk_get import BulkGetDomainsAction
from ai.backend.manager.services.domain.processors import DomainProcessors
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


class _Domains:
    """The two domains the read names, and the user who belongs to one of them."""

    own: DomainID
    other: DomainID
    user_id: UserID

    def __init__(self, own: DomainID, other: DomainID, user_id: UserID) -> None:
        self.own = own
        self.other = other
        self.user_id = user_id


@pytest.fixture
async def db(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, _WITH_TABLES):
        yield database_connection


@pytest.fixture
async def domains(db: ExtendedAsyncSAEngine) -> _Domains:
    """Two domains in the graph, and a user holding the member role in one of them."""
    seeder = VirtualEntitySeeder()
    own = DomainID(uuid.uuid4())
    other = DomainID(uuid.uuid4())
    user_id = UserID(uuid.uuid4())
    own_name = f"own-{own.hex[:8]}"
    other_name = f"other-{other.hex[:8]}"

    async with db.begin_session() as sess:
        sess.add_all([
            DomainRow(id=own, name=own_name, total_resource_slots=ResourceSlot()),
            DomainRow(id=other, name=other_name, total_resource_slots=ResourceSlot()),
        ])
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
        user = UserRow(
            uuid=user_id,
            username=f"user-{user_id.hex[:8]}",
            email=f"user-{user_id.hex[:8]}@test.com",
            resource_policy=policy_name,
            status=UserStatus.ACTIVE,
            need_password_change=False,
            sudo_session_enabled=False,
            domain_name=own_name,
            domain_id=own,
            role=UserRole.USER,
        )
        sess.add(user)
        await sess.flush()

        await seeder.provision(sess, DomainEntityType(), own)
        await seeder.provision(sess, DomainEntityType(), other)
        await seeder.provision(sess, UserEntityType(), user_id)

        # The role the domain_member preset instantiates in a domain: READ on the
        # domain type, placed in that domain's scope.
        role = RoleRow(
            name=f"domain_member-{own.hex[:8]}",
            status=RoleStatus.ACTIVE,
            scope_type=DomainEntityType(),
            scope_id=own,
        )
        sess.add(role)
        await sess.flush()
        sess.add(
            PermissionRow(
                role_id=role.id,
                entity_type=DomainEntityType(),
                permission=Permission.READ,
            )
        )
        sess.add(UserRoleRow(user_id=user_id, role_id=role.id))
        await sess.commit()

    return _Domains(own, other, user_id)


@pytest.fixture
def processors(db: ExtendedAsyncSAEngine) -> DomainProcessors:
    """The production wiring, with the RBAC validator reading this database."""
    config_provider = MagicMock()
    config_provider.config.manager.rbac.enforcement_enabled = True
    check = RbacPermissionCheckRepository(PermissionOpsProvider(db), config_provider)
    registry: ProcessorRegistry[Any] = ProcessorRegistry(
        ProcessorDependencies(
            monitors=ActionMonitors(),
            validators=ActionValidators(
                partial_bulk=[VirtualEntityPartialBulkActionRBACValidator(check)]
            ),
            repository=OpsRepository(V2DBOpsProvider(db)),
        )
    )
    return DomainProcessors(registry.group(GroupMeta(DomainEntityType())), MagicMock())


def _member(domains: _Domains) -> UserData:
    return UserData(
        user_id=domains.user_id,
        is_authorized=True,
        is_admin=False,
        is_superadmin=False,
        role=UserRole.USER,
        domain_name="own",
        domain_id=domains.own,
    )


async def test_a_member_reads_their_own_domain(
    processors: DomainProcessors,
    domains: _Domains,
) -> None:
    with with_user(_member(domains)):
        result = await processors.bulk_get.run(
            BulkGetDomainsAction(ids=[domains.own, domains.other])
        )

    assert domains.own in result.values()
    assert result.values()[domains.own].id == domains.own


async def test_a_member_is_denied_a_domain_they_hold_no_role_in(
    processors: DomainProcessors,
    domains: _Domains,
) -> None:
    with with_user(_member(domains)):
        result = await processors.bulk_get.run(
            BulkGetDomainsAction(ids=[domains.own, domains.other])
        )

    assert domains.other not in result.values()
    assert isinstance(result.errors()[domains.other], NotEnoughPermission)
