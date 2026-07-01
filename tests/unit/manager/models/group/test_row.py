"""Tests for group/row.py utility functions."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.types import ResourceSlot, VFolderHostPermissionMap

# ORM relationship cluster registration: SQLAlchemy's global
# configure_mappers() must resolve every string relationship reachable from
# the rows this isolated test registers, so the whole domain cluster is
# imported here. _ORM_CLUSTER below keeps these imports from being pruned.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.association_container_registries_groups import (
    AssociationContainerRegistriesGroupsRow,
)
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.deployment_auto_scaling_policy import DeploymentAutoScalingPolicyRow
from ai.backend.manager.models.deployment_policy import DeploymentPolicyRow
from ai.backend.manager.models.deployment_revision import DeploymentRevisionRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.group.row import resolve_group_name_or_id
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.network import NetworkRow
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.rbac_models import (
    AssociationScopesEntitiesRow,
    ObjectPermissionRow,
    RoleRow,
    UserRoleRow,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    DeploymentRevisionResourceSlotRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.runtime_variant_preset import RuntimeVariantPresetRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import VFolderInvitationRow, VFolderPermissionRow, VFolderRow
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentResourceRow,
    AgentRow,
    AssocGroupUserRow,
    AssociationContainerRegistriesGroupsRow,
    AssociationScopesEntitiesRow,
    ContainerRegistryRow,
    DeploymentAutoScalingPolicyRow,
    DeploymentPolicyRow,
    DeploymentRevisionResourceSlotRow,
    DeploymentRevisionRow,
    DomainFairShareRow,
    DomainRow,
    DomainUsageBucketRow,
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
    GroupRow,
    ImageAliasRow,
    ImageRow,
    KernelRow,
    KernelUsageRecordRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    NetworkRow,
    NotificationChannelRow,
    NotificationRuleRow,
    ObjectPermissionRow,
    ProjectFairShareRow,
    ProjectResourcePolicyRow,
    ProjectUsageBucketRow,
    ReplicaGroupRow,
    ResourcePresetRow,
    ResourceSlotTypeRow,
    RoleRow,
    RoutingRow,
    RuntimeVariantPresetRow,
    RuntimeVariantRow,
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
    SessionRow,
    UserFairShareRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
    UserUsageBucketRow,
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)


class TestResolveGroupNameOrId:
    """Tests for resolve_group_name_or_id() function - BA-5411."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with tables created."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                GroupRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def test_resource_policy(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create a test resource policy."""
        policy_name = f"test-policy-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            policy = ProjectResourcePolicyRow(
                name=policy_name,
                max_vfolder_count=10,
                max_quota_scope_size=-1,
                max_network_count=5,
            )
            session.add(policy)
            await session.commit()
        return policy_name

    @pytest.fixture
    async def test_domain(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> str:
        """Create a test domain."""
        domain_name = f"test-domain-{uuid.uuid4().hex[:8]}"
        async with db_with_cleanup.begin_session() as session:
            domain = DomainRow(
                name=domain_name,
                description="Test domain",
                is_active=True,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "4", "mem": "8g"}, None),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                allowed_docker_registries=[],
                dotfiles=b"",
                integration_id=None,
            )
            session.add(domain)
            await session.commit()
        return domain_name

    @pytest.fixture
    async def test_group_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_resource_policy: str,
    ) -> uuid.UUID:
        """Create a test group and return its UUID."""
        group_id = uuid.uuid4()
        async with db_with_cleanup.begin_session() as session:
            group = GroupRow(
                id=group_id,
                name="test-group",
                description="Test group",
                is_active=True,
                domain_name=test_domain,
                total_resource_slots=ResourceSlot.from_user_input({"cpu": "2", "mem": "4g"}, None),
                allowed_vfolder_hosts=VFolderHostPermissionMap(),
                integration_id=None,
                resource_policy=test_resource_policy,
            )
            session.add(group)
            await session.commit()
        return group_id

    async def test_resolve_with_uuid_object(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_group_uuid: uuid.UUID,
    ) -> None:
        """Test resolve_group_name_or_id() with uuid.UUID object input."""
        async with db_with_cleanup.begin_readonly() as conn:
            result = await resolve_group_name_or_id(conn, test_domain, test_group_uuid)
            assert result == test_group_uuid

    async def test_resolve_with_uuid_string(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_group_uuid: uuid.UUID,
    ) -> None:
        """Test resolve_group_name_or_id() with UUID string input (BA-5411 fix)."""
        uuid_string = str(test_group_uuid)
        async with db_with_cleanup.begin_readonly() as conn:
            result = await resolve_group_name_or_id(conn, test_domain, uuid_string)
            # Should resolve by ID, not by name
            assert result == test_group_uuid

    async def test_resolve_with_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_group_uuid: uuid.UUID,
    ) -> None:
        """Test resolve_group_name_or_id() with plain group name input."""
        group_name = "test-group"
        async with db_with_cleanup.begin_readonly() as conn:
            result = await resolve_group_name_or_id(conn, test_domain, group_name)
            # Should resolve by name
            assert result == test_group_uuid

    async def test_resolve_with_invalid_uuid_string_treated_as_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_group_uuid: uuid.UUID,
    ) -> None:
        """Test resolve_group_name_or_id() with invalid UUID-like string (treated as name)."""
        invalid_uuid_string = "550e8400-xxxx-41d4-a716-446655440000"
        async with db_with_cleanup.begin_readonly() as conn:
            result = await resolve_group_name_or_id(conn, test_domain, invalid_uuid_string)
            # Should be treated as a name (not found)
            assert result is None

    async def test_resolve_with_nonexistent_group_name(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_group_uuid: uuid.UUID,
    ) -> None:
        """Test resolve_group_name_or_id() with nonexistent group name."""
        async with db_with_cleanup.begin_readonly() as conn:
            result = await resolve_group_name_or_id(conn, test_domain, "nonexistent-group")
            # Should return None for nonexistent group
            assert result is None

    async def test_resolve_with_nonexistent_uuid(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_group_uuid: uuid.UUID,
    ) -> None:
        """Test resolve_group_name_or_id() with nonexistent UUID."""
        nonexistent_uuid = uuid.uuid4()
        async with db_with_cleanup.begin_readonly() as conn:
            result = await resolve_group_name_or_id(conn, test_domain, nonexistent_uuid)
            # Should return None for nonexistent UUID
            assert result is None

    async def test_resolve_with_nonexistent_uuid_string(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        test_domain: str,
        test_group_uuid: uuid.UUID,
    ) -> None:
        """Test resolve_group_name_or_id() with nonexistent UUID string (BA-5411)."""
        nonexistent_uuid_string = str(uuid.uuid4())
        async with db_with_cleanup.begin_readonly() as conn:
            result = await resolve_group_name_or_id(conn, test_domain, nonexistent_uuid_string)
            # Should return None for nonexistent UUID string
            assert result is None
