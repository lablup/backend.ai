"""
Tests for BaseRevisionGenerator implementation.
"""

from dataclasses import dataclass
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    DefinitionFiles,
    ExecutionSpec,
    ImageEnvironment,
    ImageIdentifierDraft,
    ModelRevisionSpecDraft,
    ModelServiceDefinition,
    MountMetadata,
    ResourceSpecDraft,
)
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.revision_generator.base import BaseRevisionGenerator


@dataclass
class _RequestSpec:
    """API request specification."""

    image: Optional[str]
    architecture: Optional[str]
    resource_slots: Optional[dict[str, Any]]
    environ: Optional[dict[str, str]]


@dataclass
class _ExpectedResult:
    """Expected result after merge."""

    image: str
    architecture: str
    resource_slots: dict[str, Any]
    environ: Optional[dict[str, str]]


@dataclass
class _LoadServiceDefinitionTestCase:
    """Test case for load_service_definition."""

    id: str
    service_definition_dict: dict[str, Any]
    runtime_variant: str
    expected: _ExpectedResult


class TestLoadServiceDefinition:
    """Test load_service_definition method - Root level + Runtime variant merge."""

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        """Mock deployment repository."""
        return MagicMock(spec=DeploymentRepository)

    @pytest.fixture
    def base_generator(self, mock_deployment_repository: MagicMock) -> BaseRevisionGenerator:
        """Create base revision generator for testing."""
        return BaseRevisionGenerator(mock_deployment_repository)

    @pytest.fixture
    def vfolder_id(self) -> UUID:
        """Test vfolder ID."""
        return uuid4()

    @pytest.mark.parametrize(
        "test_case",
        [
            _LoadServiceDefinitionTestCase(
                id="root_level_only",
                service_definition_dict={
                    "environment": {
                        "image": "default-image:latest",
                        "architecture": "x86_64",
                    },
                    "resource_slots": {
                        "cpu": 4,
                        "mem": "16gb",
                    },
                    "environ": {
                        "MY_VAR": "default",
                    },
                },
                runtime_variant="vllm",
                expected=_ExpectedResult(
                    image="default-image:latest",
                    architecture="x86_64",
                    resource_slots={"cpu": 4, "mem": "16gb"},
                    environ={"MY_VAR": "default"},
                ),
            ),
            _LoadServiceDefinitionTestCase(
                id="variant_section_only",
                service_definition_dict={
                    "vllm": {
                        "environment": {
                            "image": "vllm-image:latest",
                            "architecture": "aarch64",
                        },
                        "resource_slots": {
                            "cpu": 8,
                            "mem": "32gb",
                        },
                        "environ": {
                            "VLLM_VAR": "vllm-value",
                        },
                    },
                },
                runtime_variant="vllm",
                expected=_ExpectedResult(
                    image="vllm-image:latest",
                    architecture="aarch64",
                    resource_slots={"cpu": 8, "mem": "32gb"},
                    environ={"VLLM_VAR": "vllm-value"},
                ),
            ),
            _LoadServiceDefinitionTestCase(
                id="field_level_merge_partial_override",
                service_definition_dict={
                    # Root level (base)
                    "environment": {
                        "image": "default-image:latest",
                        "architecture": "x86_64",
                    },
                    "resource_slots": {
                        "cpu": 4,
                        "mem": "16gb",
                    },
                    "environ": {
                        "MY_VAR": "default",
                    },
                    # Variant section (overrides only cpu, adds VLLM_SPECIFIC)
                    "vllm": {
                        "environment": {
                            "image": "vllm-optimized:latest",
                        },
                        "resource_slots": {
                            "cpu": 8,
                        },
                        "environ": {
                            "VLLM_SPECIFIC": "true",
                        },
                    },
                },
                runtime_variant="vllm",
                expected=_ExpectedResult(
                    image="vllm-optimized:latest",  # from vllm
                    architecture="x86_64",  # from root
                    resource_slots={"cpu": 8, "mem": "16gb"},  # cpu from vllm, mem from root
                    environ={"MY_VAR": "default", "VLLM_SPECIFIC": "true"},  # merged
                ),
            ),
            _LoadServiceDefinitionTestCase(
                id="other_variant_sections_filtered_out",
                service_definition_dict={
                    # Root level
                    "environment": {
                        "image": "default-image:latest",
                        "architecture": "x86_64",
                    },
                    "resource_slots": {
                        "cpu": 4,
                        "mem": "16gb",
                    },
                    # sglang section (should be filtered out)
                    "sglang": {
                        "environment": {
                            "image": "custom-image:latest",
                        },
                        "resource_slots": {
                            "cpu": 12,
                        },
                    },
                    # vllm section (should be used)
                    "vllm": {
                        "resource_slots": {
                            "cpu": 8,
                        },
                    },
                },
                runtime_variant="vllm",
                expected=_ExpectedResult(
                    image="default-image:latest",  # from root
                    architecture="x86_64",  # from root
                    resource_slots={"cpu": 8, "mem": "16gb"},  # cpu from vllm, mem from root
                    environ=None,
                ),
            ),
        ],
        ids=lambda tc: tc.id,
    )
    @pytest.mark.asyncio
    async def test_load_service_definition(
        self,
        test_case: _LoadServiceDefinitionTestCase,
        base_generator: BaseRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        """Test load_service_definition with various override scenarios."""
        # Given: Service definition
        mock_deployment_repository.fetch_definition_files = AsyncMock(
            return_value=DefinitionFiles(
                model_definition={},
                service_definition=test_case.service_definition_dict,
            )
        )

        # When: Loading service definition
        result = await base_generator.load_service_definition(
            vfolder_id=vfolder_id,
            model_definition_path=None,
            runtime_variant=test_case.runtime_variant,
        )

        # Then: Should match expected values
        assert result is not None
        assert result.environment is not None
        assert result.environment.image == test_case.expected.image
        assert result.environment.architecture == test_case.expected.architecture
        assert result.resource_slots == test_case.expected.resource_slots
        assert result.environ == test_case.expected.environ

    @pytest.mark.asyncio
    async def test_no_service_definition(
        self,
        base_generator: BaseRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        """Test when service definition is None."""
        # Given: No service definition
        mock_deployment_repository.fetch_definition_files = AsyncMock(
            return_value=DefinitionFiles(
                model_definition={},
                service_definition=None,
            )
        )

        # When: Loading service definition
        result = await base_generator.load_service_definition(
            vfolder_id=vfolder_id,
            model_definition_path=None,
            runtime_variant="vllm",
        )

        # Then: Should return None
        assert result is None


@dataclass
class _MergeRevisionTestCase:
    """Test case for merge_revision."""

    id: str
    service_definition: Optional[ModelServiceDefinition]
    request: _RequestSpec
    expected: _ExpectedResult


class TestMergeRevision:
    """Test merge_revision and _override_revision - Service definition + API request merge."""

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        """Mock deployment repository."""
        return MagicMock(spec=DeploymentRepository)

    @pytest.fixture
    def base_generator(self, mock_deployment_repository: MagicMock) -> BaseRevisionGenerator:
        """Create base revision generator for testing."""
        return BaseRevisionGenerator(mock_deployment_repository)

    @pytest.fixture
    def base_mount_metadata(self) -> MountMetadata:
        """Basic mount metadata for testing."""
        return MountMetadata(
            model_vfolder_id=uuid4(),
            model_mount_destination="/models",
            model_definition_path=None,
            extra_mounts=[],
        )

    @pytest.mark.parametrize(
        "test_case",
        [
            _MergeRevisionTestCase(
                id="no_service_definition_api_request_only",
                service_definition=None,
                request=_RequestSpec(
                    image="request-image:latest",
                    architecture="aarch64",
                    resource_slots={"cpu": 2, "mem": "4gb"},
                    environ={"REQUEST_VAR": "request-value"},
                ),
                expected=_ExpectedResult(
                    image="request-image:latest",
                    architecture="aarch64",
                    resource_slots={"cpu": 2, "mem": "4gb"},
                    environ={"REQUEST_VAR": "request-value"},
                ),
            ),
            _MergeRevisionTestCase(
                id="service_definition_only_api_request_omits_optional_fields",
                service_definition=ModelServiceDefinition(
                    environment=ImageEnvironment(
                        image="service-image:v1",
                        architecture="x86_64",
                    ),
                    resource_slots={"cpu": 4, "mem": "8gb", "cuda.device": 1},
                    environ={"SERVICE_VAR": "service-value"},
                ),
                request=_RequestSpec(
                    image=None,
                    architecture=None,
                    resource_slots=None,
                    environ=None,
                ),
                expected=_ExpectedResult(
                    image="service-image:v1",
                    architecture="x86_64",
                    resource_slots={"cpu": 4, "mem": "8gb", "cuda.device": 1},
                    environ={"SERVICE_VAR": "service-value"},
                ),
            ),
            _MergeRevisionTestCase(
                id="field_level_override_api_request_overrides_service_definition",
                service_definition=ModelServiceDefinition(
                    environment=ImageEnvironment(
                        image="service-image:v1",
                        architecture="x86_64",
                    ),
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ={"SERVICE_VAR": "service-value"},
                ),
                request=_RequestSpec(
                    image="request-image:latest",  # Override
                    architecture=None,  # Use service definition
                    resource_slots={"cpu": 2},  # Override cpu only
                    environ={"REQUEST_VAR": "request-value"},  # Merge with service
                ),
                expected=_ExpectedResult(
                    image="request-image:latest",
                    architecture="x86_64",
                    resource_slots={
                        "cpu": 2,
                        "mem": "8gb",
                    },  # cpu from request, mem from service
                    environ={
                        "SERVICE_VAR": "service-value",
                        "REQUEST_VAR": "request-value",
                    },  # merged
                ),
            ),
        ],
        ids=lambda tc: tc.id,
    )
    def test_merge_revision(
        self,
        test_case: _MergeRevisionTestCase,
        base_generator: BaseRevisionGenerator,
        base_mount_metadata: MountMetadata,
    ) -> None:
        """Test merge_revision with various override scenarios."""
        # Given: API request
        draft_revision = ModelRevisionSpecDraft(
            image_identifier=ImageIdentifierDraft(
                canonical=test_case.request.image,
                architecture=test_case.request.architecture,
            ),
            resource_spec=ResourceSpecDraft(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots=test_case.request.resource_slots,
                resource_opts=None,
            ),
            mounts=base_mount_metadata,
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant.VLLM,
                startup_command="python -m vllm",
                bootstrap_script=None,
                environ=test_case.request.environ,
            ),
        )

        # When: Merging
        result = base_generator.merge_revision(draft_revision, test_case.service_definition)

        # Then: Should match expected values
        assert result.image_identifier.canonical == test_case.expected.image
        assert result.image_identifier.architecture == test_case.expected.architecture
        assert result.resource_spec.resource_slots == test_case.expected.resource_slots
        assert result.execution.environ == test_case.expected.environ


@dataclass
class _CompletePipelineTestCase:
    """Test case for complete pipeline."""

    id: str
    service_definition_dict: dict[str, Any]
    runtime_variant: str
    request: _RequestSpec
    expected: _ExpectedResult


class TestCompleteOverridePipeline:
    """Test complete override pipeline: Root → Variant → Request."""

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        """Mock deployment repository."""
        return MagicMock(spec=DeploymentRepository)

    @pytest.fixture
    def base_generator(self, mock_deployment_repository: MagicMock) -> BaseRevisionGenerator:
        """Create base revision generator for testing."""
        return BaseRevisionGenerator(mock_deployment_repository)

    @pytest.fixture
    def vfolder_id(self) -> UUID:
        """Test vfolder ID."""
        return uuid4()

    @pytest.fixture
    def base_mount_metadata(self, vfolder_id: UUID) -> MountMetadata:
        """Basic mount metadata for testing."""
        return MountMetadata(
            model_vfolder_id=vfolder_id,
            model_mount_destination="/models",
            model_definition_path="service-definition.toml",
            extra_mounts=[],
        )

    @pytest.mark.parametrize(
        "test_case",
        [
            _CompletePipelineTestCase(
                id="complete_pipeline_all_three_stages",
                service_definition_dict={
                    # Root level (base)
                    "environment": {
                        "image": "default-image:latest",
                        "architecture": "x86_64",
                    },
                    "resource_slots": {
                        "cpu": 4,
                        "mem": "16gb",
                    },
                    "environ": {
                        "ROOT_VAR": "root-value",
                    },
                    # vllm variant (overrides cpu, adds VLLM_VAR)
                    "vllm": {
                        "environment": {
                            "image": "vllm-optimized:latest",
                        },
                        "resource_slots": {
                            "cpu": 8,
                        },
                        "environ": {
                            "VLLM_VAR": "vllm-value",
                        },
                    },
                },
                runtime_variant="vllm",
                request=_RequestSpec(
                    image="request-image:latest",  # Override vllm's image
                    architecture=None,  # Use from service definition
                    resource_slots={"cpu": 2},  # Override vllm's cpu again
                    environ={"REQUEST_VAR": "request-value"},
                ),
                expected=_ExpectedResult(
                    image="request-image:latest",  # from request
                    architecture="x86_64",  # from root
                    resource_slots={
                        "cpu": 2,
                        "mem": "16gb",
                    },  # cpu from request, mem from root
                    environ={
                        "ROOT_VAR": "root-value",
                        "VLLM_VAR": "vllm-value",
                        "REQUEST_VAR": "request-value",
                    },  # all merged
                ),
            ),
            _CompletePipelineTestCase(
                id="verify_priority_order",
                service_definition_dict={
                    # Root level
                    "environment": {
                        "image": "root-image:latest",
                        "architecture": "x86_64",
                    },
                    "resource_slots": {
                        "cpu": 4,
                    },
                    # vllm variant (should override root)
                    "vllm": {
                        "environment": {
                            "image": "vllm-image:latest",
                        },
                        "resource_slots": {
                            "cpu": 8,
                        },
                    },
                },
                runtime_variant="vllm",
                request=_RequestSpec(
                    image="request-image:latest",  # Should have highest priority
                    architecture="aarch64",  # Override root's x86_64
                    resource_slots={"cpu": 2},  # Override vllm's 8
                    environ=None,
                ),
                expected=_ExpectedResult(
                    image="request-image:latest",  # request > vllm > root
                    architecture="aarch64",  # request > root
                    resource_slots={"cpu": 2},  # request > vllm > root
                    environ=None,
                ),
            ),
        ],
        ids=lambda tc: tc.id,
    )
    @pytest.mark.asyncio
    async def test_complete_pipeline(
        self,
        test_case: _CompletePipelineTestCase,
        base_generator: BaseRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
        base_mount_metadata: MountMetadata,
    ) -> None:
        """Test complete pipeline: Root → Variant → Request."""
        # Given: Service definition
        mock_deployment_repository.fetch_definition_files = AsyncMock(
            return_value=DefinitionFiles(
                model_definition={},
                service_definition=test_case.service_definition_dict,
            )
        )

        # And: API request
        requested_revision = ModelRevisionSpecDraft(
            image_identifier=ImageIdentifierDraft(
                canonical=test_case.request.image,
                architecture=test_case.request.architecture,
            ),
            resource_spec=ResourceSpecDraft(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots=test_case.request.resource_slots,
                resource_opts=None,
            ),
            mounts=base_mount_metadata,
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant.VLLM,
                startup_command="python -m vllm",
                bootstrap_script=None,
                environ=test_case.request.environ,
            ),
        )

        # When: Generating revision (complete pipeline)
        result = await base_generator.generate_revision(
            draft_revision=requested_revision,
            vfolder_id=vfolder_id,
            model_definition_path="service-definition.toml",
        )

        # Then: Should match expected values
        assert result.image_identifier.canonical == test_case.expected.image
        assert result.image_identifier.architecture == test_case.expected.architecture
        assert result.resource_spec.resource_slots == test_case.expected.resource_slots
        assert result.execution.environ == test_case.expected.environ
