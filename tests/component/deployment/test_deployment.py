"""
Component tests for deployment query and read operations.

These tests verify HTTP routing, request/response serialization,
and read-only query behavior for Deployment API endpoints via the Client SDK.
"""

from __future__ import annotations

import secrets
import uuid
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.endpoint.types import EndpointLifecycle
from ai.backend.common.data.model_deployment.types import DeploymentStrategy, ModelDeploymentStatus
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.manager.deployment import (
    CreateDeploymentRequest,
    DeactivateRevisionResponse,
    DeploymentFilter,
    DeploymentMetadataInput,
    DeploymentStrategyInput,
    ImageInput,
    ListDeploymentsResponse,
    ListRevisionsResponse,
    ListRoutesResponse,
    ModelMountConfigInput,
    ModelRuntimeConfigInput,
    NetworkAccessInput,
    ResourceConfigInput,
    RevisionInput,
    SearchDeploymentsRequest,
    SearchRevisionsRequest,
    SearchRoutesRequest,
)
from ai.backend.common.dto.manager.deployment.request import ClusterConfigInput
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.deployment.request import (
    AdminSearchDeploymentsInput,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    DeploymentFilter as DeploymentFilterV2,
)
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.resource_group import ResourceGroupName
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.types import ClusterMode
from ai.backend.manager.api.adapters.deployment.adapter import DeploymentAdapter
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import _map_lifecycle_to_status
from ai.backend.manager.services.processors import Processors
from ai.backend.testutils.fixtures import DomainFixtureData

if TYPE_CHECKING:
    from tests.component.conftest import UserFixtureData


class TestSearchDeployments:
    async def test_search_deployments_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search with no data returns an empty list and pagination total=0."""
        result = await admin_registry.deployment.search_deployments(
            SearchDeploymentsRequest(),
        )
        assert isinstance(result, ListDeploymentsResponse)
        assert result.deployments == []
        assert result.pagination.total == 0

    async def test_search_deployments_with_filter(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search with a name filter on empty data returns an empty list."""
        result = await admin_registry.deployment.search_deployments(
            SearchDeploymentsRequest(
                filter=DeploymentFilter(
                    name=StringFilter(contains="nonexistent"),
                ),
            ),
        )
        assert isinstance(result, ListDeploymentsResponse)
        assert result.deployments == []
        assert result.pagination.total == 0

    async def test_search_deployments_paginated(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_name: ResourceGroupName,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """Search deployments with pagination returns correct page."""
        image_id, vfolder_id = deployment_seed_data
        # Create multiple deployments
        deployment_ids = []
        for i in range(3):
            request = CreateDeploymentRequest(
                metadata=DeploymentMetadataInput(
                    project_id=group_fixture,
                    domain_name=domain_fixture.domain_name,
                    resource_group_name=scaling_group_name,
                    name=f"test-deployment-{i}-{secrets.token_hex(4)}",
                ),
                network_access=NetworkAccessInput(open_to_public=False),
                default_deployment_strategy=DeploymentStrategyInput(
                    type=DeploymentStrategy.ROLLING,
                ),
                replica_count=1,
                initial_revision=RevisionInput(
                    cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                    resource_config=ResourceConfigInput(
                        resource_slots={"cpu": "2", "mem": "2147483648"},
                    ),
                    image=ImageInput(id=image_id),
                    model_runtime_config=ModelRuntimeConfigInput(),
                    model_mount_config=ModelMountConfigInput(
                        vfolder_id=vfolder_id,
                        mount_destination="/models",
                        definition_path="model-definition.yaml",
                    ),
                    model_definition=ModelDefinitionDraft(),
                ),
            )
            response = await admin_registry.deployment.create_deployment(request)
            deployment_ids.append(response.deployment.id)

        # Search with pagination
        result = await admin_registry.deployment.search_deployments(
            SearchDeploymentsRequest(limit=2, offset=0),
        )
        assert isinstance(result, ListDeploymentsResponse)
        assert len(result.deployments) >= 2
        assert result.pagination.total >= 3


class TestGetDeployment:
    async def test_get_deployment_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """GET a non-existent deployment UUID returns a proper error response."""
        non_existent_id = uuid.uuid4()
        with pytest.raises(NotFoundError):
            await admin_registry.deployment.get_deployment(non_existent_id)

    async def test_get_deployment_by_id(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_name: ResourceGroupName,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """Get deployment by ID returns correct deployment details."""
        image_id, vfolder_id = deployment_seed_data
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture.domain_name,
                resource_group_name=scaling_group_name,
                name=f"test-deployment-{secrets.token_hex(4)}",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            replica_count=1,
            initial_revision=RevisionInput(
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_slots={"cpu": "2", "mem": "2147483648"},
                ),
                image=ImageInput(id=image_id),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
                model_definition=ModelDefinitionDraft(),
            ),
        )
        response = await admin_registry.deployment.create_deployment(request)
        deployment = response.deployment

        # Get by ID
        fetched_response = await admin_registry.deployment.get_deployment(deployment.id)
        fetched = fetched_response.deployment
        assert fetched.id == deployment.id
        assert fetched.name == deployment.name
        assert fetched.project_id == group_fixture


class TestSearchRevisions:
    async def test_search_revisions_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search revisions for a non-existent deployment returns empty results."""
        non_existent_deployment_id = uuid.uuid4()
        result = await admin_registry.deployment.search_revisions(
            non_existent_deployment_id,
            SearchRevisionsRequest(),
        )
        assert isinstance(result, ListRevisionsResponse)
        assert result.revisions == []
        assert result.pagination.total == 0

    async def test_search_revisions_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search revisions with custom pagination returns correct pagination info."""
        random_deployment_id = uuid.uuid4()
        result = await admin_registry.deployment.search_revisions(
            random_deployment_id,
            SearchRevisionsRequest(limit=10, offset=0),
        )
        assert isinstance(result, ListRevisionsResponse)
        assert result.revisions == []
        assert result.pagination.total == 0
        assert result.pagination.limit == 10
        assert result.pagination.offset == 0


class TestSearchRoutes:
    async def test_search_routes_empty(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search routes for a non-existent deployment returns empty results."""
        non_existent_deployment_id = uuid.uuid4()
        result = await admin_registry.deployment.search_routes(
            non_existent_deployment_id,
            SearchRoutesRequest(),
        )
        assert isinstance(result, ListRoutesResponse)
        assert result.routes == []
        assert result.pagination.total_count == 0

    async def test_search_routes_for_nonexistent_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Searching routes for a non-existent deployment returns empty results."""
        random_deployment_id = uuid.uuid4()
        result = await admin_registry.deployment.search_routes(
            random_deployment_id,
            SearchRoutesRequest(),
        )
        assert isinstance(result, ListRoutesResponse)
        assert result.routes == []
        assert result.pagination.total_count == 0
        assert result.pagination.has_next_page is False
        assert result.pagination.has_previous_page is False

    async def test_search_routes_for_deployment(
        self,
        admin_registry: BackendAIClientRegistry,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_name: ResourceGroupName,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """Search routes for a deployment returns route list."""
        image_id, vfolder_id = deployment_seed_data
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=group_fixture,
                domain_name=domain_fixture.domain_name,
                resource_group_name=scaling_group_name,
                name=f"test-deployment-{secrets.token_hex(4)}",
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            replica_count=1,
            initial_revision=RevisionInput(
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_slots={"cpu": "2", "mem": "2147483648"},
                ),
                image=ImageInput(id=image_id),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
                model_definition=ModelDefinitionDraft(),
            ),
        )
        response = await admin_registry.deployment.create_deployment(request)
        deployment = response.deployment

        # Search routes
        routes_result = await admin_registry.deployment.search_routes(
            deployment.id,
            SearchRoutesRequest(limit=10, offset=0),
        )
        assert routes_result is not None
        # Routes may be empty if not yet created, but API should succeed
        assert hasattr(routes_result, "routes")


class TestDeactivateRevision:
    async def test_deactivate_revision_stub(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Deactivate always returns success=True (stub handler)."""
        fake_deployment_id = uuid.uuid4()
        fake_revision_id = uuid.uuid4()
        result = await admin_registry.deployment.deactivate_revision(
            fake_deployment_id,
            fake_revision_id,
        )
        assert isinstance(result, DeactivateRevisionResponse)
        assert result.success is True


class TestDeploymentAdapterFilter:
    """Verify the GQL adapter honors AND/OR/NOT in DeploymentFilter.

    The adapter's ``my_search`` and ``project_search`` previously inlined
    the filter conversion and silently dropped nested ``AND``/``OR``/``NOT``
    clauses, so multi-condition filters degenerated into "no filter at all".
    These tests pin the corrected behavior.
    """

    @pytest.fixture
    def deployment_adapter(
        self,
        deployment_processors: DeploymentProcessors,
    ) -> DeploymentAdapter:
        processors_mock = MagicMock(spec=Processors)
        processors_mock.deployment = deployment_processors
        return DeploymentAdapter(processors_mock, deployment_coordinator=MagicMock())

    @staticmethod
    def _admin_user_data(user_uuid: uuid.UUID, domain: str) -> UserData:
        return UserData(
            user_id=user_uuid,
            is_authorized=True,
            is_admin=True,
            is_superadmin=True,
            role=UserRole.SUPERADMIN,
            domain_name=domain,
        )

    @staticmethod
    async def _create_deployment_with_tags(
        admin_registry: BackendAIClientRegistry,
        project_id: uuid.UUID,
        domain: str,
        scaling_group: ResourceGroupName,
        seed_data: tuple[ImageID, VFolderUUID],
        tags: list[str],
        name: str | None = None,
    ) -> uuid.UUID:
        image_id, vfolder_id = seed_data
        request = CreateDeploymentRequest(
            metadata=DeploymentMetadataInput(
                project_id=project_id,
                domain_name=domain,
                resource_group_name=scaling_group,
                name=name or f"test-deployment-{secrets.token_hex(4)}",
                tags=tags,
            ),
            network_access=NetworkAccessInput(open_to_public=False),
            default_deployment_strategy=DeploymentStrategyInput(
                type=DeploymentStrategy.ROLLING,
            ),
            replica_count=1,
            initial_revision=RevisionInput(
                cluster_config=ClusterConfigInput(mode=ClusterMode.SINGLE_NODE, size=1),
                resource_config=ResourceConfigInput(
                    resource_slots={"cpu": "2", "mem": "2147483648"},
                ),
                image=ImageInput(id=image_id),
                model_runtime_config=ModelRuntimeConfigInput(),
                model_mount_config=ModelMountConfigInput(
                    vfolder_id=vfolder_id,
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                ),
                model_definition=ModelDefinitionDraft(),
            ),
        )
        response = await admin_registry.deployment.create_deployment(request)
        return response.deployment.id

    async def test_my_search_and_filter_returns_intersection(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_user_fixture: UserFixtureData,
        deployment_adapter: DeploymentAdapter,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_name: ResourceGroupName,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """AND clause must narrow results to deployments matching every nested filter."""
        await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["alpha", "production"],
        )
        await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["beta", "production"],
        )
        target_id = await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["alpha", "beta"],
        )

        filter_input = DeploymentFilterV2(
            AND=[
                DeploymentFilterV2(tags=StringFilter(i_contains="alpha")),
                DeploymentFilterV2(tags=StringFilter(i_contains="beta")),
            ],
        )
        with with_user(
            self._admin_user_data(admin_user_fixture.user_uuid, domain_fixture.domain_name)
        ):
            payload = await deployment_adapter.my_search(
                AdminSearchDeploymentsInput(filter=filter_input, limit=50),
            )

        assert payload.total_count == 1
        assert [item.id for item in payload.items] == [target_id]

    async def test_my_search_or_filter_returns_union(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_user_fixture: UserFixtureData,
        deployment_adapter: DeploymentAdapter,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_name: ResourceGroupName,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """OR clause must widen results to deployments matching any nested filter."""
        alpha_id = await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["alpha"],
        )
        beta_id = await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["beta"],
        )
        await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["gamma"],
        )

        filter_input = DeploymentFilterV2(
            OR=[
                DeploymentFilterV2(tags=StringFilter(i_contains="alpha")),
                DeploymentFilterV2(tags=StringFilter(i_contains="beta")),
            ],
        )
        with with_user(
            self._admin_user_data(admin_user_fixture.user_uuid, domain_fixture.domain_name)
        ):
            payload = await deployment_adapter.my_search(
                AdminSearchDeploymentsInput(filter=filter_input, limit=50),
            )

        assert payload.total_count == 2
        assert {item.id for item in payload.items} == {alpha_id, beta_id}

    async def test_my_search_or_filter_groups_multi_field_subfilters(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_user_fixture: UserFixtureData,
        deployment_adapter: DeploymentAdapter,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_name: ResourceGroupName,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """OR with multi-field sub-filters must AND fields within each branch.

        Pins ``(A AND B) OR (C AND D)`` semantics: each OR sub-filter is an AND
        of its own fields, then the sub-filters are OR'd. A regression that
        flattens sub-conditions would degenerate into ``A OR B OR C OR D`` and
        return rows that match neither full branch.
        """
        suffix = secrets.token_hex(4)
        branch1_id = await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["alpha"],
            name=f"bar-x-{suffix}",
        )
        branch2_id = await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["beta"],
            name=f"foo-x-{suffix}",
        )
        await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["beta"],
            name=f"bar-y-{suffix}",
        )
        await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["alpha"],
            name=f"foo-y-{suffix}",
        )

        filter_input = DeploymentFilterV2(
            OR=[
                DeploymentFilterV2(
                    name=StringFilter(i_contains="bar"),
                    tags=StringFilter(i_contains="alpha"),
                ),
                DeploymentFilterV2(
                    name=StringFilter(i_contains="foo"),
                    tags=StringFilter(i_contains="beta"),
                ),
            ],
        )
        with with_user(
            self._admin_user_data(admin_user_fixture.user_uuid, domain_fixture.domain_name)
        ):
            payload = await deployment_adapter.my_search(
                AdminSearchDeploymentsInput(filter=filter_input, limit=50),
            )

        assert payload.total_count == 2
        assert {item.id for item in payload.items} == {branch1_id, branch2_id}

    async def test_project_search_and_filter_returns_intersection(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_user_fixture: UserFixtureData,
        deployment_adapter: DeploymentAdapter,
        group_fixture: uuid.UUID,
        domain_fixture: DomainFixtureData,
        scaling_group_name: ResourceGroupName,
        deployment_seed_data: tuple[ImageID, VFolderUUID],
    ) -> None:
        """project_search must also honor AND across nested filters."""
        await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["alpha"],
        )
        target_id = await self._create_deployment_with_tags(
            admin_registry,
            group_fixture,
            domain_fixture.domain_name,
            scaling_group_name,
            deployment_seed_data,
            ["alpha", "beta"],
        )

        filter_input = DeploymentFilterV2(
            AND=[
                DeploymentFilterV2(tags=StringFilter(i_contains="alpha")),
                DeploymentFilterV2(tags=StringFilter(i_contains="beta")),
            ],
        )
        with with_user(
            self._admin_user_data(admin_user_fixture.user_uuid, domain_fixture.domain_name)
        ):
            payload = await deployment_adapter.project_search(
                group_fixture,
                AdminSearchDeploymentsInput(filter=filter_input, limit=50),
            )

        assert payload.total_count == 1
        assert [item.id for item in payload.items] == [target_id]


class TestStatusMapping:
    def test_lifecycle_to_status_mapping(self) -> None:
        """Verify EndpointLifecycle maps correctly to ModelDeploymentStatus.

        After the scaling_state split, the lifecycle axis is monotonic and
        SCALING is no longer surfaced through ModelDeploymentStatus — legacy
        ``lifecycle=SCALING`` rows fold into READY. Replica reconciliation is
        exposed via the orthogonal ``scaling_state`` field on the deployment
        node instead. The deprecated ``lifecycle=CREATED`` (never-deployed)
        folds into PENDING.
        """
        mapping = {
            EndpointLifecycle.PENDING: ModelDeploymentStatus.PENDING,
            EndpointLifecycle.CREATED: ModelDeploymentStatus.PENDING,
            EndpointLifecycle.READY: ModelDeploymentStatus.READY,
            EndpointLifecycle.SCALING: ModelDeploymentStatus.READY,
            EndpointLifecycle.DEPLOYING: ModelDeploymentStatus.DEPLOYING,
            EndpointLifecycle.DESTROYING: ModelDeploymentStatus.STOPPING,
            EndpointLifecycle.DESTROYED: ModelDeploymentStatus.STOPPED,
        }

        for lifecycle, expected_status in mapping.items():
            actual_status = _map_lifecycle_to_status(lifecycle)
            assert actual_status == expected_status, (
                f"EndpointLifecycle.{lifecycle.name} should map to "
                f"ModelDeploymentStatus.{expected_status.name}, got {actual_status.name}"
            )
