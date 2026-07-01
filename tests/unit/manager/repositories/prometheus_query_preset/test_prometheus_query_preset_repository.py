"""Tests for PrometheusQueryPresetRepository CRUD operations."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.dto.clients.prometheus.response import (
    PrometheusQueryData,
    PrometheusResponse,
)
from ai.backend.common.exception import (
    FailedToGetMetric,
    PrometheusQueryEvaluationFailed,
    PrometheusQueryPresetNotFound,
)
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.data.prometheus_query_preset import (
    PrometheusQueryPresetData,
)

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry, so the forward-reachable rows below must be imported. Kept live by
# the _ORM_CLUSTER reference.
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
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.image import ImageAliasRow, ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.network import NetworkRow
from ai.backend.manager.models.prometheus_query_preset import PrometheusQueryPresetRow
from ai.backend.manager.models.prometheus_query_preset.row import PresetOptions
from ai.backend.manager.models.prometheus_query_preset_category import (
    PrometheusQueryPresetCategoryRow,
)
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
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
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
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    Creator,
    OffsetPagination,
)
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.prometheus_query_preset import (
    PrometheusQueryPresetCreatorSpec,
    PrometheusQueryPresetRepository,
)
from ai.backend.manager.repositories.prometheus_query_preset.updaters import (
    PrometheusQueryPresetUpdaterSpec,
)
from ai.backend.manager.types import OptionalState, TriState
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
    DomainRow,
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
    GroupRow,
    ImageAliasRow,
    ImageRow,
    KernelRow,
    KeyPairResourcePolicyRow,
    KeyPairRow,
    NetworkRow,
    ObjectPermissionRow,
    ProjectResourcePolicyRow,
    ReplicaGroupRow,
    ResourcePresetRow,
    ResourceSlotTypeRow,
    RoleRow,
    RoutingRow,
    RuntimeVariantRow,
    ScalingGroupForDomainRow,
    ScalingGroupForKeypairsRow,
    ScalingGroupForProjectRow,
    ScalingGroupRow,
    SessionRow,
    UserResourcePolicyRow,
    UserRoleRow,
    UserRow,
    VFolderInvitationRow,
    VFolderPermissionRow,
    VFolderRow,
)


class TestPrometheusQueryPresetRepository:
    """Test cases for PrometheusQueryPresetRepository CRUD operations."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [PrometheusQueryPresetCategoryRow, PrometheusQueryPresetRow],
        ):
            yield database_connection

    @pytest.fixture
    def preset_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> PrometheusQueryPresetRepository:
        return PrometheusQueryPresetRepository(
            db=db_with_cleanup,
            prometheus_client=MagicMock(spec=PrometheusClient),
        )

    @pytest.fixture
    async def sample_preset_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> uuid.UUID:
        """Create a sample preset directly in DB and return its ID."""
        preset_id = uuid.uuid4()
        now = datetime.now(tz=UTC)
        async with db_with_cleanup.begin_session() as db_sess:
            row = PrometheusQueryPresetRow(
                id=preset_id,
                name="container_cpu_rate",
                metric_name="backendai_container_utilization",
                query_template="sum by ({group_by})(rate({metric_name}{{{labels}}}[{window}]))",
                time_window="5m",
                options=PresetOptions(
                    filter_labels=["container_metric_name", "kernel_id"],
                    group_labels=["kernel_id"],
                ),
                created_at=now,
                updated_at=now,
            )
            db_sess.add(row)
            await db_sess.flush()
        return preset_id

    @pytest.fixture
    async def sample_preset_ids(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> list[uuid.UUID]:
        """Create 5 sample presets directly in DB and return their IDs."""
        preset_ids: list[uuid.UUID] = []
        now = datetime.now(tz=UTC)
        async with db_with_cleanup.begin_session() as db_sess:
            for i in range(5):
                preset_id = uuid.uuid4()
                preset_ids.append(preset_id)
                row = PrometheusQueryPresetRow(
                    id=preset_id,
                    name=f"preset_{i}",
                    metric_name="backendai_metric",
                    query_template="template",
                    time_window=None,
                    options=PresetOptions(filter_labels=[], group_labels=[]),
                    created_at=now,
                    updated_at=now,
                )
                db_sess.add(row)
            await db_sess.flush()
        return preset_ids

    async def test_create(
        self,
        preset_repository: PrometheusQueryPresetRepository,
    ) -> None:
        name = "gpu_memory_usage"
        metric_name = "backendai_gpu_memory"
        query_template = "avg({metric_name}{{{labels}}})"
        time_window = "10m"
        filter_labels = ["kernel_id", "device_id"]
        group_labels = ["kernel_id"]

        creator = Creator(
            spec=PrometheusQueryPresetCreatorSpec(
                name=name,
                metric_name=metric_name,
                query_template=query_template,
                time_window=time_window,
                filter_labels=filter_labels,
                group_labels=group_labels,
            ),
        )

        result = await preset_repository.create(creator)

        assert isinstance(result, PrometheusQueryPresetData)
        assert result.name == name
        assert result.metric_name == metric_name
        assert result.query_template == query_template
        assert result.time_window == time_window
        assert result.filter_labels == filter_labels
        assert result.group_labels == group_labels
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

    async def test_get_by_id(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        result = await preset_repository.get_by_id(sample_preset_id)

        assert result.id == sample_preset_id
        assert result.name == "container_cpu_rate"
        assert result.metric_name == "backendai_container_utilization"
        assert result.time_window == "5m"
        assert result.filter_labels == ["container_metric_name", "kernel_id"]
        assert result.group_labels == ["kernel_id"]

    async def test_get_by_id_not_found(
        self,
        preset_repository: PrometheusQueryPresetRepository,
    ) -> None:
        with pytest.raises(PrometheusQueryPresetNotFound):
            await preset_repository.get_by_id(uuid.uuid4())

    async def test_search(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_ids: list[uuid.UUID],
    ) -> None:
        limit = 3
        querier = BatchQuerier(
            pagination=OffsetPagination(limit=limit, offset=0),
            conditions=[],
            orders=[],
        )
        result = await preset_repository.search(querier=querier)

        assert len(result.items) == limit
        assert result.total_count == len(sample_preset_ids)

    async def test_update(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        updated_name = "updated_preset"
        updated_metric_name = "new_metric"

        updater_spec = PrometheusQueryPresetUpdaterSpec(
            name=OptionalState[str].update(updated_name),
            metric_name=OptionalState[str].update(updated_metric_name),
            time_window=TriState[str].nullify(),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_preset_id)

        result = await preset_repository.update(updater=updater)

        assert result.name == updated_name
        assert result.metric_name == updated_metric_name
        assert result.time_window is None

    async def test_update_filter_labels_only_preserves_group_labels(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        original = await preset_repository.get_by_id(sample_preset_id)

        updated_filter_labels = ["updated_filter"]
        updater_spec = PrometheusQueryPresetUpdaterSpec(
            filter_labels=OptionalState[list[str]].update(updated_filter_labels),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_preset_id)

        result = await preset_repository.update(updater=updater)

        assert result.filter_labels == updated_filter_labels
        assert result.group_labels == original.group_labels

    async def test_update_group_labels_only_preserves_filter_labels(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        original = await preset_repository.get_by_id(sample_preset_id)

        updated_group_labels = ["updated_group"]
        updater_spec = PrometheusQueryPresetUpdaterSpec(
            group_labels=OptionalState[list[str]].update(updated_group_labels),
        )
        updater = Updater(spec=updater_spec, pk_value=sample_preset_id)

        result = await preset_repository.update(updater=updater)

        assert result.group_labels == updated_group_labels
        assert result.filter_labels == original.filter_labels

    async def test_delete(
        self,
        preset_repository: PrometheusQueryPresetRepository,
        sample_preset_id: uuid.UUID,
    ) -> None:
        result = await preset_repository.delete(sample_preset_id)
        assert result is True

        with pytest.raises(PrometheusQueryPresetNotFound):
            await preset_repository.get_by_id(sample_preset_id)

    async def test_delete_not_found(
        self,
        preset_repository: PrometheusQueryPresetRepository,
    ) -> None:
        with pytest.raises(PrometheusQueryPresetNotFound):
            await preset_repository.delete(uuid.uuid4())


class TestPrometheusQueryPresetRepositoryPreview:
    """Tests for preview_query_template — does not touch DB."""

    @pytest.fixture
    def canned_response(self) -> PrometheusResponse:
        return PrometheusResponse(
            status="success",
            data=PrometheusQueryData(result_type="vector", result=[]),
        )

    @pytest.fixture
    def prometheus_client(self, canned_response: PrometheusResponse) -> MagicMock:
        client = MagicMock(spec=PrometheusClient)
        client.preview_query_template = AsyncMock(return_value=canned_response)
        return client

    @pytest.fixture
    def repository(
        self,
        prometheus_client: MagicMock,
    ) -> PrometheusQueryPresetRepository:
        return PrometheusQueryPresetRepository(
            db=MagicMock(),
            prometheus_client=prometheus_client,
        )

    async def test_delegates_to_client_with_template_and_window(
        self,
        repository: PrometheusQueryPresetRepository,
        prometheus_client: MagicMock,
        canned_response: PrometheusResponse,
    ) -> None:
        result = await repository.preview_template(
            query_template="sum(rate(metric{{{labels}}}[{window}]))",
            default_window="5m",
        )

        prometheus_client.preview_query_template.assert_called_once_with(
            query_template="sum(rate(metric{{{labels}}}[{window}]))",
            default_window="5m",
        )
        assert result is canned_response

    async def test_converts_failed_to_get_metric_to_evaluation_failed(
        self,
        repository: PrometheusQueryPresetRepository,
        prometheus_client: MagicMock,
    ) -> None:
        prometheus_client.preview_query_template = AsyncMock(
            side_effect=FailedToGetMetric('parse error: unexpected "}" (status=400, path=query)'),
        )

        with pytest.raises(PrometheusQueryEvaluationFailed):
            await repository.preview_template(
                query_template="sum({invalid",
                default_window="5m",
            )
