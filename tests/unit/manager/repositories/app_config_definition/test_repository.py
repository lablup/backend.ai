"""Tests for AppConfigDefinitionRepository with real database operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.common.identifier.app_config_definition import AppConfigDefinitionID
from ai.backend.manager.data.app_config_definition.types import AppConfigDefinitionData
from ai.backend.manager.errors.app_config import AppConfigDefinitionNotFound

# ORM relationship cluster registration: SQLAlchemy's global
# configure_mappers() must resolve every string relationship reachable from
# the rows this isolated test registers, so the whole domain cluster is
# imported here. _ORM_CLUSTER below keeps these imports from being pruned.
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.app_config_definition.conditions import (
    AppConfigDefinitionConditions,
)
from ai.backend.manager.models.app_config_definition.orders import AppConfigDefinitionOrders
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
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
from ai.backend.manager.repositories.app_config_definition.creators import (
    AppConfigDefinitionCreatorSpec,
)
from ai.backend.manager.repositories.app_config_definition.repository import (
    AppConfigDefinitionRepository,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    CursorForwardPagination,
    OffsetPagination,
    Purger,
)
from ai.backend.manager.repositories.ops import DBOpsProvider
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


@pytest.fixture
async def repository(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[AppConfigDefinitionRepository, None]:
    async with with_tables(database_connection, [AppConfigDefinitionRow]):
        yield AppConfigDefinitionRepository(DBOpsProvider(database_connection))


@pytest.fixture
async def existing_definition(
    repository: AppConfigDefinitionRepository,
) -> AppConfigDefinitionData:
    return await repository.create(Creator(spec=AppConfigDefinitionCreatorSpec(config_name="menu")))


@pytest.fixture
async def seeded_definitions(
    repository: AppConfigDefinitionRepository,
) -> list[AppConfigDefinitionData]:
    definitions: list[AppConfigDefinitionData] = []
    for config_name in ("theme", "menu", "preferences"):
        definition = await repository.create(
            Creator(spec=AppConfigDefinitionCreatorSpec(config_name=config_name))
        )
        definitions.append(definition)
    return definitions


def _missing_id() -> AppConfigDefinitionID:
    return AppConfigDefinitionID(uuid.uuid4())


class TestCreateAndGet:
    async def test_create_then_get_by_id(self, repository: AppConfigDefinitionRepository) -> None:
        created = await repository.create(
            Creator(spec=AppConfigDefinitionCreatorSpec(config_name="theme"))
        )
        fetched = await repository.get_by_id(created.id)
        assert fetched.id == created.id
        assert fetched.config_name == "theme"

    async def test_get_by_id_missing_raises(
        self, repository: AppConfigDefinitionRepository
    ) -> None:
        with pytest.raises(AppConfigDefinitionNotFound):
            await repository.get_by_id(_missing_id())


class TestPurge:
    async def test_purge_removes_row(
        self,
        repository: AppConfigDefinitionRepository,
        existing_definition: AppConfigDefinitionData,
    ) -> None:
        purged = await repository.purge(
            Purger(row_class=AppConfigDefinitionRow, pk_value=existing_definition.id)
        )
        assert purged.id == existing_definition.id
        with pytest.raises(AppConfigDefinitionNotFound):
            await repository.get_by_id(existing_definition.id)

    async def test_purge_missing_raises(self, repository: AppConfigDefinitionRepository) -> None:
        with pytest.raises(AppConfigDefinitionNotFound):
            await repository.purge(Purger(row_class=AppConfigDefinitionRow, pk_value=_missing_id()))


class TestSearch:
    async def test_search_returns_all_with_total_count(
        self,
        repository: AppConfigDefinitionRepository,
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(pagination=OffsetPagination(limit=10, offset=0))
        )
        assert result.total_count == len(seeded_definitions)
        assert {item.config_name for item in result.items} == {
            definition.config_name for definition in seeded_definitions
        }

    async def test_search_respects_pagination(
        self,
        repository: AppConfigDefinitionRepository,
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(pagination=OffsetPagination(limit=2, offset=0))
        )
        assert result.total_count == len(seeded_definitions)
        assert len(result.items) == 2
        assert result.has_next_page is True

    async def test_search_filters_by_config_name(
        self,
        repository: AppConfigDefinitionRepository,
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[
                    AppConfigDefinitionConditions.by_config_name_equals(
                        StringMatchSpec("menu", case_insensitive=False, negated=False)
                    )
                ],
            )
        )
        expected = [
            definition.config_name
            for definition in seeded_definitions
            if definition.config_name == "menu"
        ]
        assert result.total_count == len(expected)
        assert [item.config_name for item in result.items] == expected

    async def test_search_orders_by_config_name_desc(
        self,
        repository: AppConfigDefinitionRepository,
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                orders=[AppConfigDefinitionOrders.config_name(ascending=False)],
            )
        )
        expected = sorted(
            (definition.config_name for definition in seeded_definitions), reverse=True
        )
        assert [item.config_name for item in result.items] == expected

    async def test_search_filters_by_created_at(
        self,
        repository: AppConfigDefinitionRepository,
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        target = seeded_definitions[1]
        result = await repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                conditions=[AppConfigDefinitionConditions.by_created_at_equals(target.created_at)],
            )
        )
        assert [item.id for item in result.items] == [target.id]

    async def test_search_orders_by_created_at(
        self,
        repository: AppConfigDefinitionRepository,
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        result = await repository.search(
            BatchQuerier(
                pagination=OffsetPagination(limit=10, offset=0),
                orders=[AppConfigDefinitionOrders.created_at(ascending=True)],
            )
        )
        expected = [
            definition.id for definition in sorted(seeded_definitions, key=lambda d: d.created_at)
        ]
        assert [item.id for item in result.items] == expected

    async def test_search_cursor_forward(
        self,
        repository: AppConfigDefinitionRepository,
        seeded_definitions: list[AppConfigDefinitionData],
    ) -> None:
        by_created_desc = sorted(seeded_definitions, key=lambda d: d.created_at, reverse=True)
        cursor = by_created_desc[0].id
        result = await repository.search(
            BatchQuerier(
                pagination=CursorForwardPagination(
                    first=10,
                    cursor_order=AppConfigDefinitionOrders.created_at(ascending=False),
                    cursor_condition=AppConfigDefinitionConditions.by_cursor_forward(str(cursor)),
                )
            )
        )
        assert [item.id for item in result.items] == [d.id for d in by_created_desc[1:]]
