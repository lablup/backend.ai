"""
Service layer tests for service definition merge behavior during deployment creation.

These tests verify the acceptance criteria from BA-3030:
1. Service creation with only service-definition.toml
2. Service creation with only API request
3. Service creation with both (override behavior)
4. Validation errors for missing required fields in final config

The tests use the definition generator pattern which is the actual code path
that merges service definition with API request.
"""

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    DefinitionFiles,
    ExecutionSpec,
    MountMetadata,
    RequestedImageIdentifier,
    RequestedModelRevisionSpec,
    RequestedResourceSpec,
)
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.definition_generator.custom import (
    CustomModelDefinitionGenerator,
)


@dataclass
class RequestData:
    """Test data for API request."""

    image: str | None
    architecture: str | None
    resource_slots: dict | None
    cluster_mode: ClusterMode
    cluster_size: int


@dataclass
class ExpectedResult:
    """Expected result after merge."""

    image: str
    architecture: str
    resource_slots: dict
    cluster_mode: ClusterMode
    cluster_size: int


@dataclass
class MergeTestCase:
    """Test case for service definition merge."""

    service_def_dict: dict | None
    request: RequestData
    expected: ExpectedResult


@dataclass
class ErrorTestCase:
    """Test case for validation errors."""

    service_def_dict: dict
    request: RequestData
    expected_error_match: str


class TestServiceDefinitionMerge:
    """
    Test service definition merge behavior matching acceptance criteria.

    1. API requests can omit image and architecture when defined in service-definition.toml
    2. service-definition.toml values are used as base configuration
    3. API request values properly override service-definition.toml values
    4. Final merged configuration is validated before service creation
    """

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        """Mock deployment repository."""
        return MagicMock(spec=DeploymentRepository)

    @pytest.fixture
    def custom_definition_generator(
        self,
        mock_deployment_repository: MagicMock,
    ) -> CustomModelDefinitionGenerator:
        """Create a custom definition generator for testing."""
        return CustomModelDefinitionGenerator(
            deployment_repository=mock_deployment_repository,
        )

    @pytest.fixture
    def base_execution_spec(self) -> ExecutionSpec:
        """Basic execution spec for testing."""
        return ExecutionSpec(
            startup_command="python -m server",
            bootstrap_script=None,
            environ=None,
            runtime_variant=RuntimeVariant.CUSTOM,
        )

    @pytest.fixture
    def base_mount_metadata(self) -> MountMetadata:
        """Basic mount metadata for testing."""
        return MountMetadata(
            model_vfolder_id=uuid4(),
            model_mount_destination="/models",
            model_definition_path="service-definition.toml",
            extra_mounts=[],
        )

    @pytest.fixture
    def minimal_model_definition(self) -> dict:
        """Minimal valid model definition."""
        return {
            "model": {
                "name": "test-model",
                "version": "1.0",
            }
        }

    @pytest.mark.parametrize(
        "test_case",
        [
            # Only service definition - API request omits all optional fields
            MergeTestCase(
                service_def_dict={
                    "environment": {"image": "registry.com/model:v1", "architecture": "x86_64"},
                    "resource_slots": {"cpu": "4", "mem": "8g", "cuda.device": "1"},
                    "environ": {"MODEL_TYPE": "llm"},
                },
                request=RequestData(
                    image=None,
                    architecture=None,
                    resource_slots=None,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                expected=ExpectedResult(
                    image="registry.com/model:v1",
                    architecture="x86_64",
                    resource_slots={"cpu": "4", "mem": "8g", "cuda.device": "1"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ),
            # Only API request - no service definition
            MergeTestCase(
                service_def_dict=None,
                request=RequestData(
                    image="request-image:latest",
                    architecture="arm64",
                    resource_slots={"cpu": "2", "mem": "4g"},
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=2,
                ),
                expected=ExpectedResult(
                    image="request-image:latest",
                    architecture="arm64",
                    resource_slots={"cpu": "2", "mem": "4g"},
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=2,
                ),
            ),
            # Both - service definition overrides request
            MergeTestCase(
                service_def_dict={
                    "environment": {"image": "service-image:v2", "architecture": "arm64"},
                    "resource_slots": {"cpu": "8", "mem": "16g"},
                    "environ": {"MODEL_TYPE": "llm"},
                },
                request=RequestData(
                    image="request-image:v1",
                    architecture="x86_64",
                    resource_slots={"cpu": "2", "mem": "4g"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                expected=ExpectedResult(
                    image="service-image:v2",
                    architecture="arm64",
                    resource_slots={"cpu": "8", "mem": "16g"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ),
            # Partial override - only image from service definition
            MergeTestCase(
                service_def_dict={
                    "environment": {"image": "service-image:v1", "architecture": "arm64"}
                },
                request=RequestData(
                    image="request-image:v1",
                    architecture="x86_64",
                    resource_slots={"cpu": "2", "mem": "4g"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                expected=ExpectedResult(
                    image="service-image:v1",
                    architecture="arm64",
                    resource_slots={"cpu": "2", "mem": "4g"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ),
            # Partial override - only resource slots from service definition
            MergeTestCase(
                service_def_dict={"resource_slots": {"cpu": "4", "mem": "8g"}},
                request=RequestData(
                    image="request-image:latest",
                    architecture="x86_64",
                    resource_slots={"cpu": "2", "mem": "4g"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                expected=ExpectedResult(
                    image="request-image:latest",
                    architecture="x86_64",
                    resource_slots={"cpu": "4", "mem": "8g"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ),
        ],
        ids=[
            "only_service_definition",
            "only_api_request",
            "both_override",
            "partial_override_image",
            "partial_override_slots",
        ],
    )
    @pytest.mark.asyncio
    async def test_service_definition_merge_success(
        self,
        custom_definition_generator: CustomModelDefinitionGenerator,
        mock_deployment_repository: MagicMock,
        base_execution_spec: ExecutionSpec,
        base_mount_metadata: MountMetadata,
        minimal_model_definition: dict,
        test_case: MergeTestCase,
    ) -> None:
        """Test successful service definition merge scenarios."""
        # Given: An API request
        requested_spec = RequestedModelRevisionSpec(
            image_identifier=RequestedImageIdentifier(
                canonical=test_case.request.image,
                architecture=test_case.request.architecture,
            ),
            resource_spec=RequestedResourceSpec(
                cluster_mode=test_case.request.cluster_mode,
                cluster_size=test_case.request.cluster_size,
                resource_slots=test_case.request.resource_slots,
            ),
            mounts=base_mount_metadata,
            execution=base_execution_spec,
        )

        # And: Repository returns definition files
        mock_deployment_repository.fetch_definition_files = AsyncMock(
            return_value=DefinitionFiles(
                model_definition=minimal_model_definition,
                service_definition=test_case.service_def_dict,
            )
        )

        # When: Generating model revision
        result = await custom_definition_generator.generate_model_revision(requested_spec)

        # Then: Final config should match expected values
        assert result.image_identifier.canonical == test_case.expected.image
        assert result.image_identifier.architecture == test_case.expected.architecture
        assert result.resource_spec.resource_slots == test_case.expected.resource_slots
        assert result.resource_spec.cluster_mode == test_case.expected.cluster_mode
        assert result.resource_spec.cluster_size == test_case.expected.cluster_size

    @pytest.mark.parametrize(
        "test_case",
        [
            # Missing image canonical and architecture in both
            ErrorTestCase(
                service_def_dict={"resource_slots": {"cpu": "4", "mem": "8g"}},
                request=RequestData(
                    image=None,
                    architecture=None,
                    resource_slots={"cpu": "2", "mem": "4g"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                expected_error_match="Image canonical and architecture",
            ),
            # Missing resource slots in both
            ErrorTestCase(
                service_def_dict={
                    "environment": {"image": "service-image:v1", "architecture": "x86_64"}
                },
                request=RequestData(
                    image="request-image:latest",
                    architecture="x86_64",
                    resource_slots=None,
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                expected_error_match="Resource slots must be specified in either requested model revision or model service definition",
            ),
            # Missing architecture in both
            ErrorTestCase(
                service_def_dict={"resource_slots": {"cpu": "4", "mem": "8g"}},
                request=RequestData(
                    image="request-image:latest",
                    architecture=None,
                    resource_slots={"cpu": "2", "mem": "4g"},
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                expected_error_match="Image architecture must be specified",
            ),
        ],
        ids=[
            "missing_image_canonical_and_architecture",
            "missing_resource_slots",
            "missing_architecture",
        ],
    )
    @pytest.mark.asyncio
    async def test_validation_error_missing_required_fields(
        self,
        custom_definition_generator: CustomModelDefinitionGenerator,
        mock_deployment_repository: MagicMock,
        base_execution_spec: ExecutionSpec,
        base_mount_metadata: MountMetadata,
        minimal_model_definition: dict,
        test_case: ErrorTestCase,
    ) -> None:
        """Test validation errors when required fields are missing in both sources."""
        # Given: An API request with missing fields
        requested_spec = RequestedModelRevisionSpec(
            image_identifier=RequestedImageIdentifier(
                canonical=test_case.request.image,
                architecture=test_case.request.architecture,
            ),
            resource_spec=RequestedResourceSpec(
                cluster_mode=test_case.request.cluster_mode,
                cluster_size=test_case.request.cluster_size,
                resource_slots=test_case.request.resource_slots,
            ),
            mounts=base_mount_metadata,
            execution=base_execution_spec,
        )

        # And: Repository returns definition files
        mock_deployment_repository.fetch_definition_files = AsyncMock(
            return_value=DefinitionFiles(
                model_definition=minimal_model_definition,
                service_definition=test_case.service_def_dict,
            )
        )

        # When/Then: Generating model revision should raise error
        with pytest.raises(InvalidAPIParameters, match=test_case.expected_error_match):
            await custom_definition_generator.generate_model_revision(requested_spec)
