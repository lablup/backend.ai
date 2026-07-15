"""
Mock-based unit tests for DeploymentService.

Tests verify service layer business logic using mocked repositories.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from typing import cast, override
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.config import ModelDefinitionDraft
from ai.backend.common.contexts.user import with_user
from ai.backend.common.data.endpoint.types import EndpointLifecycle, ScalingState
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.data.user.types import UserData, UserRole
from ai.backend.common.dto.appproxy_coordinator.v2.endpoint.response import (
    MintEndpointTokenResponse,
)
from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.common.schema.deployment import BlueGreenSpec, IntOrPercent, RollingUpdateSpec
from ai.backend.common.types import ClusterMode, MountPermission, ResourceSlot
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.actions.validators.rbac.bulk import BulkActionRBACValidator
from ai.backend.manager.actions.validators.rbac.scope import ScopeActionRBACValidator
from ai.backend.manager.actions.validators.rbac.single_entity import (
    SingleEntityActionRBACValidator,
)
from ai.backend.manager.clients.appproxy.client import AppProxyClient, AppProxyClientPool
from ai.backend.manager.data.deployment.access_token import ModelDeploymentAccessTokenCreator
from ai.backend.manager.data.deployment.creator import (
    ModelRevisionCreator,
    VFolderMountsCreator,
)
from ai.backend.manager.data.deployment.types import (
    ClusterConfigData,
    DeploymentInfo,
    DeploymentMetadata,
    DeploymentNetworkData,
    DeploymentOptions,
    DeploymentPolicyData,
    DeploymentPolicySearchResult,
    DeploymentPolicyUpsertResult,
    DeploymentState,
    ExecutionData,
    ExecutionSpec,
    ModelMountConfigData,
    ModelRevisionData,
    ModelRuntimeConfigData,
    PresetAttributionData,
    ReplicaData,
    ResourceConfigData,
    ResourceSpec,
)
from ai.backend.manager.data.deployment.upserter import DeploymentPolicyUpserter
from ai.backend.manager.data.resource.types import ScalingGroupProxyTarget
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.base.rbac.entity_creator import RBACEntityCreator
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.repositories.deployment.creators import EndpointTokenCreatorSpec
from ai.backend.manager.services.deployment.actions.access_token.create_access_token import (
    CreateAccessTokenAction,
)
from ai.backend.manager.services.deployment.actions.deployment_policy import (
    SearchDeploymentPoliciesAction,
    UpsertDeploymentPolicyAction,
)
from ai.backend.manager.services.deployment.actions.model_revision.add_model_revision import (
    AddModelRevisionAction,
)
from ai.backend.manager.services.deployment.processors import DeploymentProcessors
from ai.backend.manager.services.deployment.service import (
    DeploymentService,
    _convert_deployment_info_to_data,
    _convert_deployment_info_to_legacy_data,
)
from ai.backend.manager.sokovan.deployment import DeploymentController


class DeploymentServiceBaseFixtures:
    """Base class containing shared fixtures for deployment service tests."""

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        """Mock DeploymentRepository for testing."""
        return MagicMock(spec=DeploymentRepository)

    @pytest.fixture
    def mock_deployment_controller(self) -> MagicMock:
        """Mock DeploymentController for testing."""
        return MagicMock(spec=DeploymentController)

    @pytest.fixture
    def mock_appproxy_client_pool(self) -> MagicMock:
        """Mock AppProxyClientPool for testing."""
        return MagicMock(spec=AppProxyClientPool)

    @pytest.fixture
    def deployment_service(
        self,
        mock_deployment_controller: MagicMock,
        mock_deployment_repository: MagicMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> DeploymentService:
        """Create DeploymentService with mock dependencies."""
        return DeploymentService(
            deployment_controller=mock_deployment_controller,
            deployment_repository=mock_deployment_repository,
            appproxy_client_pool=mock_appproxy_client_pool,
        )

    @pytest.fixture
    def processors(self, deployment_service: DeploymentService) -> DeploymentProcessors:
        """Create DeploymentProcessors with mock DeploymentService."""
        return DeploymentProcessors(
            deployment_service,
            [],
            ActionValidators(
                rbac=RBACValidators(
                    scope=MagicMock(spec=ScopeActionRBACValidator),
                    single_entity=MagicMock(spec=SingleEntityActionRBACValidator),
                    bulk=MagicMock(spec=BulkActionRBACValidator),
                ),
            ),
        )

    @pytest.fixture
    def deployment_policy_data(self) -> DeploymentPolicyData:
        """Sample deployment policy data for testing."""
        return DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=uuid.uuid4(),
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(
                max_surge=IntOrPercent(count=1),
                max_unavailable=IntOrPercent(count=0),
            ),
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )

    @pytest.fixture
    def endpoint_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def policy_id(self) -> uuid.UUID:
        return uuid.uuid4()


class TestUpsertDeploymentPolicy(DeploymentServiceBaseFixtures):
    """Tests for DeploymentService.upsert_deployment_policy"""

    @pytest.fixture
    def rolling_upserter(self, endpoint_id: uuid.UUID) -> DeploymentPolicyUpserter:
        return DeploymentPolicyUpserter(
            deployment_id=endpoint_id,
            strategy=DeploymentStrategy.ROLLING,
            strategy_spec=RollingUpdateSpec(
                max_surge=IntOrPercent(count=2),
                max_unavailable=IntOrPercent(count=1),
            ),
        )

    @pytest.fixture
    def blue_green_upserter(self, endpoint_id: uuid.UUID) -> DeploymentPolicyUpserter:
        return DeploymentPolicyUpserter(
            deployment_id=endpoint_id,
            strategy=DeploymentStrategy.BLUE_GREEN,
            strategy_spec=BlueGreenSpec(auto_promote=True, promote_delay_seconds=30),
        )

    @pytest.fixture
    def blue_green_policy_data(self) -> DeploymentPolicyData:
        return DeploymentPolicyData(
            id=uuid.uuid4(),
            endpoint=uuid.uuid4(),
            strategy=DeploymentStrategy.BLUE_GREEN,
            strategy_spec=BlueGreenSpec(auto_promote=True, promote_delay_seconds=30),
            created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC),
        )

    async def test_upsert_deployment_policy_insert(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        endpoint_id: uuid.UUID,
        rolling_upserter: DeploymentPolicyUpserter,
    ) -> None:
        """Upsert should create a new policy when none exists (created=True)."""
        mock_deployment_repository.upsert_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyUpsertResult(data=deployment_policy_data, created=True)
        )

        action = UpsertDeploymentPolicyAction(upserter=rolling_upserter)

        result = await processors.upsert_deployment_policy.wait_for_complete(action)

        assert result.created is True
        assert result.data == deployment_policy_data
        mock_deployment_repository.upsert_deployment_policy.assert_called_once()
        upserter_arg = mock_deployment_repository.upsert_deployment_policy.call_args[0][0]
        spec = upserter_arg.spec
        assert spec.deployment_id == endpoint_id
        assert spec.strategy == DeploymentStrategy.ROLLING

    async def test_upsert_deployment_policy_update(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        blue_green_upserter: DeploymentPolicyUpserter,
        blue_green_policy_data: DeploymentPolicyData,
    ) -> None:
        """Upsert should update an existing policy (created=False)."""
        mock_deployment_repository.upsert_deployment_policy = AsyncMock(
            return_value=DeploymentPolicyUpsertResult(data=blue_green_policy_data, created=False)
        )

        action = UpsertDeploymentPolicyAction(upserter=blue_green_upserter)

        result = await processors.upsert_deployment_policy.wait_for_complete(action)

        assert result.created is False
        assert result.data == blue_green_policy_data
        assert result.data.strategy == DeploymentStrategy.BLUE_GREEN


class TestSearchDeploymentPolicies(DeploymentServiceBaseFixtures):
    """Tests for DeploymentService.search_deployment_policies"""

    @pytest.fixture
    def default_querier(self) -> BatchQuerier:
        return BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[],
            orders=[],
        )

    @pytest.fixture
    def paginated_querier(self) -> BatchQuerier:
        return BatchQuerier(
            pagination=OffsetPagination(limit=10, offset=10),
            conditions=[],
            orders=[],
        )

    async def test_search_deployment_policies_success(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        default_querier: BatchQuerier,
    ) -> None:
        """Search deployment policies should return matching results."""
        mock_deployment_repository.search_deployment_policies = AsyncMock(
            return_value=DeploymentPolicySearchResult(
                items=[deployment_policy_data],
                total_count=1,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchDeploymentPoliciesAction(querier=default_querier)

        result = await processors.search_deployment_policies.wait_for_complete(action)

        assert result.data == [deployment_policy_data]
        assert result.total_count == 1
        assert result.has_next_page is False
        assert result.has_previous_page is False
        mock_deployment_repository.search_deployment_policies.assert_called_once_with(
            default_querier
        )

    async def test_search_deployment_policies_empty_result(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        default_querier: BatchQuerier,
    ) -> None:
        """Search deployment policies should return empty list when no results found."""
        mock_deployment_repository.search_deployment_policies = AsyncMock(
            return_value=DeploymentPolicySearchResult(
                items=[],
                total_count=0,
                has_next_page=False,
                has_previous_page=False,
            )
        )

        action = SearchDeploymentPoliciesAction(querier=default_querier)

        result = await processors.search_deployment_policies.wait_for_complete(action)

        assert result.data == []
        assert result.total_count == 0

    async def test_search_deployment_policies_with_pagination(
        self,
        processors: DeploymentProcessors,
        mock_deployment_repository: MagicMock,
        deployment_policy_data: DeploymentPolicyData,
        paginated_querier: BatchQuerier,
    ) -> None:
        """Search deployment policies should handle pagination correctly."""
        mock_deployment_repository.search_deployment_policies = AsyncMock(
            return_value=DeploymentPolicySearchResult(
                items=[deployment_policy_data],
                total_count=25,
                has_next_page=True,
                has_previous_page=True,
            )
        )

        action = SearchDeploymentPoliciesAction(querier=paginated_querier)

        result = await processors.search_deployment_policies.wait_for_complete(action)

        assert result.total_count == 25
        assert result.has_next_page is True
        assert result.has_previous_page is True


class ModelRevisionFixtures(DeploymentServiceBaseFixtures):
    """Fixtures for model revision tests."""

    @pytest.fixture(autouse=True)
    def _setup_default_repository_mocks(
        self,
        mock_deployment_repository: MagicMock,
        deployment_info: DeploymentInfo,
        revision_data: ModelRevisionData,
    ) -> None:
        """Set up default mock responses for repository methods used in add_model_revision."""
        mock_deployment_repository.get_endpoint_info = AsyncMock(return_value=deployment_info)
        mock_deployment_repository.create_revision_with_next_number = AsyncMock(
            return_value=revision_data
        )

    @pytest.fixture
    def deployment_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def image_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def model_vfolder_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def deployment_info(self, deployment_id: uuid.UUID) -> DeploymentInfo:
        return DeploymentInfo(
            primary_replica_group_id=ReplicaGroupID(uuid.uuid4()),
            id=DeploymentID(deployment_id),
            metadata=DeploymentMetadata(
                name="test-deployment",
                domain="default",
                project=uuid.uuid4(),
                resource_group="default",
                created_user=uuid.uuid4(),
                session_owner=uuid.uuid4(),
                created_at=datetime(2024, 1, 1, tzinfo=UTC),
                revision_history_limit=10,
            ),
            state=DeploymentState(
                lifecycle=EndpointLifecycle.READY,
                scaling_state=ScalingState.STABLE,
                retry_count=0,
            ),
            replica=ReplicaData(replica_count=1, desired_replica_count=None),
            network=DeploymentNetworkData(
                open_to_public=False, access_token_ids=None, url=None, preferred_domain_name=None
            ),
            options=DeploymentOptions(),
        )

    @pytest.fixture
    def revision_creator(
        self, image_id: uuid.UUID, model_vfolder_id: uuid.UUID
    ) -> ModelRevisionCreator:
        return ModelRevisionCreator(
            image_id=ImageID(image_id),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots={"cpu": "4", "mem": "8g"},
                resource_opts={"shmem": "1g"},
            ),
            mounts=VFolderMountsCreator(
                model_vfolder_id=VFolderUUID(model_vfolder_id),
                model_definition_path="model-definition.yaml",
                model_mount_destination="/models",
                extra_mounts=[],
                model_mount_perm=None,
            ),
            execution=ExecutionSpec(
                startup_command="python serve.py",
                bootstrap_script="pip install -r requirements.txt",
                environ={"CUDA_VISIBLE_DEVICES": "0"},
                runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
                callback_url=None,
            ),
            model_definition=ModelDefinitionDraft(),
        )

    @pytest.fixture
    def revision_data(self, image_id: uuid.UUID, model_vfolder_id: uuid.UUID) -> ModelRevisionData:
        return ModelRevisionData(
            id=DeploymentRevisionID(uuid.uuid4()),
            deployment_id=DeploymentID(uuid.uuid4()),
            revision_number=1,
            cluster_config=ClusterConfigData(
                mode=ClusterMode.SINGLE_NODE,
                size=1,
            ),
            resource_config=ResourceConfigData(
                resource_group_name="default",
                resource_slot=ResourceSlot({"cpu": "4", "mem": "8g"}),
            ),
            model_runtime_config=ModelRuntimeConfigData(
                runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
            ),
            model_mount_config=ModelMountConfigData(
                vfolder_id=VFolderUUID(model_vfolder_id),
                mount_destination="/models",
                definition_path="model-definition.yaml",
                extra_mounts=[],
                model_mount_perm=MountPermission.READ_ONLY,
            ),
            image_id=ImageID(image_id),
            execution=ExecutionData(
                startup_command=None,
                bootstrap_script=None,
                callback_url=None,
            ),
            revision_preset=PresetAttributionData(preset_id=None, values=[]),
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
        )

    @pytest.fixture
    def revision_creator_with_none_environ(
        self, image_id: uuid.UUID, model_vfolder_id: uuid.UUID
    ) -> ModelRevisionCreator:
        """Creator with None environ and resource_opts for edge case testing."""
        return ModelRevisionCreator(
            image_id=ImageID(image_id),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots={"cpu": "2"},
                resource_opts=None,
            ),
            mounts=VFolderMountsCreator(
                model_vfolder_id=VFolderUUID(model_vfolder_id),
                model_definition_path=None,
                model_mount_destination="/models",
                extra_mounts=[],
                model_mount_perm=None,
            ),
            execution=ExecutionSpec(
                runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
                environ=None,
            ),
            model_definition=ModelDefinitionDraft(),
        )


class TestAddModelRevision(ModelRevisionFixtures):
    """Tests for DeploymentService.add_model_revision — now delegates to controller."""

    @pytest.fixture
    def requester(self) -> UserData:
        return UserData(
            user_id=uuid.uuid4(),
            is_authorized=True,
            is_admin=False,
            is_superadmin=False,
            role=UserRole.USER,
            domain_name="default",
        )

    @pytest.fixture(autouse=True)
    def set_user_context(self, requester: UserData) -> Iterator[None]:
        with with_user(requester):
            yield

    async def test_add_model_revision_delegates_to_controller(
        self,
        processors: DeploymentProcessors,
        mock_deployment_controller: MagicMock,
        deployment_id: uuid.UUID,
        requester: UserData,
        revision_creator: ModelRevisionCreator,
        revision_data: ModelRevisionData,
    ) -> None:
        """add_model_revision delegates to the controller with the current user as requester.

        The service resolves the requesting user from the request context and
        forwards it as ``requester_id``; the controller owns the projection onto
        ``RevisionDraft`` + ``MountMetadata`` + ``preset_id`` and the optional
        activation step.
        """
        mock_deployment_controller.add_deployment_revision = AsyncMock(return_value=revision_data)

        action = AddModelRevisionAction(
            model_deployment_id=DeploymentID(deployment_id),
            adder=revision_creator,
            auto_activate=False,
        )
        result = await processors.add_model_revision.wait_for_complete(action)

        assert result.revision == revision_data
        mock_deployment_controller.add_deployment_revision.assert_awaited_once_with(
            deployment_id=deployment_id,
            revision=revision_creator,
            requester_id=requester.user_id,
            auto_activate=False,
        )


class TestCreateAccessToken(DeploymentServiceBaseFixtures):
    """Regression tests for DeploymentService.create_access_token (BA-5881).

    The previous implementation persisted ``secrets.token_urlsafe(32)`` as the
    deployment access token, which app-proxy worker rejects with 401 because
    it expects a coordinator-signed JWT. These tests pin the new contract:
    the service must call the app-proxy coordinator to mint a JWT, persist it
    via the CreatorSpec, and return it to the caller.
    """

    @pytest.fixture
    def deployment_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def session_owner_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def project_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def deployment_info(
        self,
        deployment_id: uuid.UUID,
        session_owner_id: uuid.UUID,
        project_id: uuid.UUID,
    ) -> DeploymentInfo:
        return DeploymentInfo(
            primary_replica_group_id=ReplicaGroupID(uuid.uuid4()),
            id=DeploymentID(deployment_id),
            metadata=DeploymentMetadata(
                name="ba5881-test",
                domain="default",
                project=project_id,
                resource_group="default",
                created_user=uuid.uuid4(),
                session_owner=session_owner_id,
                created_at=datetime(2024, 1, 1, tzinfo=UTC),
                revision_history_limit=10,
            ),
            state=DeploymentState(
                lifecycle=EndpointLifecycle.READY,
                scaling_state=ScalingState.STABLE,
                retry_count=0,
            ),
            replica=ReplicaData(replica_count=1, desired_replica_count=None),
            network=DeploymentNetworkData(
                open_to_public=False, access_token_ids=None, url=None, preferred_domain_name=None
            ),
            options=DeploymentOptions(),
        )

    @pytest.fixture
    def sample_proxy_target(self) -> ScalingGroupProxyTarget:
        return ScalingGroupProxyTarget(
            addr="http://app-proxy.local:10200",
            api_token="proxy-api-token",
        )

    @pytest.fixture
    def sample_coordinator_jwt(self) -> str:
        # The exact bytes are irrelevant; the test only cares that this string
        # round-trips from the (mocked) coordinator into the persisted token.
        return "eyJhbGciOiJIUzI1NiJ9.coordinator-signed-payload.signature"

    @pytest.fixture
    def sample_token_row(
        self,
        deployment_id: uuid.UUID,
        sample_coordinator_jwt: str,
    ) -> MagicMock:
        row = MagicMock()
        row.id = uuid.uuid4()
        row.token = sample_coordinator_jwt
        row.endpoint = DeploymentID(deployment_id)
        row.expires_at = None
        row.created_at = datetime(2024, 1, 1, tzinfo=UTC)
        return row

    @pytest.fixture
    def configure_repository(
        self,
        mock_deployment_repository: MagicMock,
        deployment_info: DeploymentInfo,
        sample_proxy_target: ScalingGroupProxyTarget,
        sample_token_row: MagicMock,
    ) -> MagicMock:
        mock_deployment_repository.get_endpoint_info = AsyncMock(return_value=deployment_info)
        mock_deployment_repository.fetch_scaling_group_proxy_targets = AsyncMock(
            return_value={deployment_info.metadata.resource_group: sample_proxy_target}
        )
        mock_deployment_repository.create_access_token = AsyncMock(return_value=sample_token_row)
        return mock_deployment_repository

    @pytest.fixture
    @override
    def mock_appproxy_client_pool(self, sample_coordinator_jwt: str) -> MagicMock:
        client = MagicMock(spec=AppProxyClient)
        client.mint_endpoint_token = AsyncMock(
            return_value=MintEndpointTokenResponse(token=sample_coordinator_jwt)
        )
        pool = MagicMock(spec=AppProxyClientPool)
        pool.load_client = MagicMock(return_value=client)
        return pool

    @pytest.fixture
    @override
    def deployment_service(
        self,
        mock_deployment_controller: MagicMock,
        mock_deployment_repository: MagicMock,
        mock_appproxy_client_pool: MagicMock,
    ) -> DeploymentService:
        return DeploymentService(
            deployment_controller=mock_deployment_controller,
            deployment_repository=mock_deployment_repository,
            appproxy_client_pool=mock_appproxy_client_pool,
        )

    async def test_persists_coordinator_jwt_instead_of_random(
        self,
        deployment_service: DeploymentService,
        configure_repository: MagicMock,
        deployment_id: uuid.UUID,
        sample_coordinator_jwt: str,
    ) -> None:
        """Regression: BA-5881. The token persisted via the CreatorSpec must
        be the JWT returned by the app-proxy coordinator, not a locally
        generated random string. If this fails, ``./bai deployment access-token
        create`` is producing tokens that app-proxy worker rejects with 401.
        """
        action = CreateAccessTokenAction(
            creator=ModelDeploymentAccessTokenCreator(
                model_deployment_id=DeploymentID(deployment_id),
                expires_at=datetime(2099, 1, 1, tzinfo=UTC),
            ),
        )
        result = await deployment_service.create_access_token(action)

        assert result.data.token == sample_coordinator_jwt

        repo_call = configure_repository.create_access_token.await_args
        assert repo_call is not None
        creator = cast(RBACEntityCreator[object], repo_call.args[0])
        spec = cast(EndpointTokenCreatorSpec, creator.spec)
        assert spec.token == sample_coordinator_jwt


class TestConvertDeploymentInfoToData:
    """Regression test for ``_convert_deployment_info_to_data`` (BA-5963)."""

    @pytest.fixture
    def make_revision_data(self) -> Callable[[int], ModelRevisionData]:
        def make(revision_number: int) -> ModelRevisionData:
            return ModelRevisionData(
                id=DeploymentRevisionID(uuid.uuid4()),
                deployment_id=DeploymentID(uuid.uuid4()),
                revision_number=revision_number,
                cluster_config=ClusterConfigData(
                    mode=ClusterMode.SINGLE_NODE,
                    size=1,
                ),
                resource_config=ResourceConfigData(
                    resource_group_name="default",
                    resource_slot=ResourceSlot({"cpu": "1"}),
                ),
                model_runtime_config=ModelRuntimeConfigData(
                    runtime_variant_id=RuntimeVariantID(uuid.uuid4()),
                ),
                model_mount_config=ModelMountConfigData(
                    vfolder_id=VFolderUUID(uuid.uuid4()),
                    mount_destination="/models",
                    definition_path="model-definition.yaml",
                    extra_mounts=[],
                    model_mount_perm=MountPermission.READ_ONLY,
                ),
                created_at=datetime(2024, 1, 1, tzinfo=UTC),
                image_id=ImageID(uuid.uuid4()),
                execution=ExecutionData(
                    startup_command=None,
                    bootstrap_script=None,
                    callback_url=None,
                ),
                revision_preset=PresetAttributionData(preset_id=None, values=[]),
            )

        return make

    def test_current_revision_resolved_by_id_match_not_list_order(
        self,
        make_revision_data: Callable[[int], ModelRevisionData],
    ) -> None:
        """Pin: revision lookup must use explicit ``current_revision_id``, not list[0]."""
        deploying_data = make_revision_data(1)
        current_data = make_revision_data(2)

        deployment_info = DeploymentInfo(
            primary_replica_group_id=ReplicaGroupID(uuid.uuid4()),
            id=DeploymentID(uuid.uuid4()),
            metadata=DeploymentMetadata(
                name="ba5963-test",
                domain="default",
                project=uuid.uuid4(),
                resource_group="default",
                created_user=uuid.uuid4(),
                session_owner=uuid.uuid4(),
                created_at=datetime(2024, 1, 1, tzinfo=UTC),
                revision_history_limit=10,
            ),
            state=DeploymentState(
                lifecycle=EndpointLifecycle.DEPLOYING,
                scaling_state=ScalingState.STABLE,
                retry_count=0,
            ),
            replica=ReplicaData(replica_count=1, desired_replica_count=None),
            network=DeploymentNetworkData(
                open_to_public=False, access_token_ids=None, url=None, preferred_domain_name=None
            ),
            options=DeploymentOptions(),
            current_revision_id=current_data.id,
            deploying_revision_id=deploying_data.id,
            current_revision=current_data,
            deploying_revision=deploying_data,
        )

        deployment_data = _convert_deployment_info_to_data(deployment_info)

        assert deployment_data.current_revision_id == current_data.id
        assert deployment_data.deploying_revision_id == deploying_data.id
        assert deployment_data.current_revision_id != deployment_data.deploying_revision_id

        # The full current revision now lives on the legacy (REST v1) projection.
        legacy_data = _convert_deployment_info_to_legacy_data(deployment_info)
        assert legacy_data.revision is not None
        assert legacy_data.revision.id == current_data.id
