"""
Tests for PermissionControllerRepository.search_element_associations() functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from ai.backend.manager.data.permission.types import EntityType, RBACElementType, ScopeType

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
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.network import NetworkRow
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.conditions import EntityScopeConditions
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
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
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
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


@dataclass
class CreatedAssociation:
    id: uuid.UUID
    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    entity_id: str
    registered_at: datetime


class TestSearchElementAssociations:
    """Tests for searching element associations."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                DomainRow,
                UserResourcePolicyRow,
                KeyPairResourcePolicyRow,
                RoleRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                PermissionRow,
                ObjectPermissionRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_rbac_tables)

    @pytest.fixture
    async def created_associations(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> list[CreatedAssociation]:
        """Create multiple entity associations for testing."""
        created: list[CreatedAssociation] = []
        base_time = datetime(2026, 1, 1, tzinfo=UTC)

        async with db_with_rbac_tables.begin_session() as db_sess:
            for i, (scope_type, scope_id, entity_type, entity_id) in enumerate([
                (ScopeType.DOMAIN, "test-domain", EntityType.USER, str(uuid.uuid4())),
                (ScopeType.DOMAIN, "test-domain", EntityType.USER, str(uuid.uuid4())),
                (ScopeType.PROJECT, str(uuid.uuid4()), EntityType.VFOLDER, str(uuid.uuid4())),
                (ScopeType.DOMAIN, "test-domain", EntityType.IMAGE, str(uuid.uuid4())),
            ]):
                registered_at = base_time + timedelta(minutes=i)
                row = AssociationScopesEntitiesRow(
                    scope_type=scope_type,
                    scope_id=scope_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    registered_at=registered_at,
                )
                db_sess.add(row)
                await db_sess.flush()
                created.append(
                    CreatedAssociation(
                        id=row.id,
                        scope_type=scope_type,
                        scope_id=scope_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        registered_at=row.registered_at,
                    )
                )

        return created

    async def test_search_element_associations_items_have_correct_data(
        self,
        repository: PermissionControllerRepository,
        created_associations: list[CreatedAssociation],
    ) -> None:
        """Returned items should contain correct scope and entity data."""
        querier = BatchQuerier(
            conditions=[
                EntityScopeConditions.by_entity_type(RBACElementType.IMAGE),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_element_associations(querier)

        assert result.total_count == 1
        item = result.items[0]
        expected = next(a for a in created_associations if a.entity_type == EntityType.IMAGE)
        assert item.object_id.entity_id == expected.entity_id
        assert item.scope_id.scope_type == expected.scope_type
        assert item.scope_id.scope_id == expected.scope_id
