"""
Tests for BaseRevisionGenerator implementation.
"""

from dataclasses import dataclass
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from ai.backend.common.exception import InvalidAPIParameters
from ai.backend.common.types import ClusterMode, RuntimeVariant
from ai.backend.manager.data.deployment.types import (
    ExecutionSpec,
    ImageEnvironment,
    ImageIdentifierDraft,
    ModelRevisionSpec,
    ModelRevisionSpecDraft,
    ModelServiceDefinition,
    MountMetadata,
    ResourceSpec,
    ResourceSpecDraft,
)
from ai.backend.manager.data.image.types import ImageIdentifier
from ai.backend.manager.errors.deployment import DefinitionFileNotFound
from ai.backend.manager.repositories.deployment import DeploymentRepository
from ai.backend.manager.sokovan.deployment.revision_generator.base import BaseRevisionGenerator
from ai.backend.manager.sokovan.deployment.revision_generator.custom import CustomRevisionGenerator


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
        mock_deployment_repository.fetch_service_definition = AsyncMock(
            return_value=test_case.service_definition_dict
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
        mock_deployment_repository.fetch_service_definition = AsyncMock(return_value=None)

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
    default_architecture: Optional[str] = None


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
            # default_architecture tests
            _MergeRevisionTestCase(
                id="default_arch_used_when_no_service_def_env",
                # No environment in service_definition means architecture comes from default
                service_definition=ModelServiceDefinition(
                    environment=None,  # No environment section
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
                ),
                request=_RequestSpec(
                    image="request-image:v1",  # Image required when no env
                    architecture=None,  # No architecture in request
                    resource_slots=None,
                    environ=None,
                ),
                default_architecture="x86_64",
                expected=_ExpectedResult(
                    image="request-image:v1",
                    architecture="x86_64",  # from default_architecture
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
                ),
            ),
            _MergeRevisionTestCase(
                id="service_def_overrides_default_arch",
                service_definition=ModelServiceDefinition(
                    environment=ImageEnvironment(
                        image="service-image:v1",
                        architecture="aarch64",  # Service definition has architecture
                    ),
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
                ),
                request=_RequestSpec(
                    image=None,
                    architecture=None,  # No architecture in request
                    resource_slots=None,
                    environ=None,
                ),
                default_architecture="x86_64",
                expected=_ExpectedResult(
                    image="service-image:v1",
                    architecture="aarch64",  # service def overrides default
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
                ),
            ),
            _MergeRevisionTestCase(
                id="request_overrides_default_arch",
                # Use environment=None so service def doesn't provide architecture
                service_definition=ModelServiceDefinition(
                    environment=None,
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
                ),
                request=_RequestSpec(
                    image="request-image:v1",
                    architecture="aarch64",  # Request has architecture
                    resource_slots=None,
                    environ=None,
                ),
                default_architecture="x86_64",
                expected=_ExpectedResult(
                    image="request-image:v1",
                    architecture="aarch64",  # request overrides default
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
                ),
            ),
            _MergeRevisionTestCase(
                id="request_overrides_all_including_default_and_service_def",
                service_definition=ModelServiceDefinition(
                    environment=ImageEnvironment(
                        image="service-image:v1",
                        architecture="arm64",  # Service definition has architecture
                    ),
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
                ),
                request=_RequestSpec(
                    image=None,
                    architecture="aarch64",  # Request has highest priority
                    resource_slots=None,
                    environ=None,
                ),
                default_architecture="x86_64",
                expected=_ExpectedResult(
                    image="service-image:v1",
                    architecture="aarch64",  # request overrides both service def and default
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
                ),
            ),
            _MergeRevisionTestCase(
                id="no_default_arch_uses_service_def",
                service_definition=ModelServiceDefinition(
                    environment=ImageEnvironment(
                        image="service-image:v1",
                        architecture="x86_64",
                    ),
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
                ),
                request=_RequestSpec(
                    image=None,
                    architecture=None,
                    resource_slots=None,
                    environ=None,
                ),
                default_architecture=None,  # No default architecture
                expected=_ExpectedResult(
                    image="service-image:v1",
                    architecture="x86_64",  # from service def
                    resource_slots={"cpu": 4, "mem": "8gb"},
                    environ=None,
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

        # When: Merging (with optional default_architecture)
        result = base_generator.merge_revision(
            draft_revision,
            test_case.service_definition,
            test_case.default_architecture,
        )

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
    default_architecture: Optional[str] = None


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
            # default_architecture tests with complete pipeline
            # Note: service_definition_dict must provide architecture since ImageEnvironment requires it
            _CompletePipelineTestCase(
                id="complete_pipeline_default_arch_overridden_by_service_def",
                service_definition_dict={
                    # Root level
                    "environment": {
                        "image": "default-image:latest",
                        "architecture": "aarch64",  # Architecture in root
                    },
                    "resource_slots": {
                        "cpu": 4,
                        "mem": "16gb",
                    },
                    # vllm variant (inherits architecture from root)
                    "vllm": {
                        "resource_slots": {
                            "cpu": 8,
                        },
                    },
                },
                runtime_variant="vllm",
                request=_RequestSpec(
                    image=None,
                    architecture=None,  # No architecture in request
                    resource_slots=None,
                    environ=None,
                ),
                default_architecture="x86_64",
                expected=_ExpectedResult(
                    image="default-image:latest",  # from root
                    architecture="aarch64",  # from service def (overrides default)
                    resource_slots={"cpu": 8, "mem": "16gb"},  # cpu from vllm, mem from root
                    environ=None,
                ),
            ),
            _CompletePipelineTestCase(
                id="complete_pipeline_default_arch_overridden_by_request",
                service_definition_dict={
                    # Root level
                    "environment": {
                        "image": "default-image:latest",
                        "architecture": "amd64",  # Provide architecture
                    },
                    "resource_slots": {
                        "cpu": 4,
                    },
                },
                runtime_variant="vllm",
                request=_RequestSpec(
                    image=None,
                    architecture="arm64",  # Request overrides service def and default
                    resource_slots=None,
                    environ=None,
                ),
                default_architecture="x86_64",
                expected=_ExpectedResult(
                    image="default-image:latest",  # from root
                    architecture="arm64",  # from request (highest priority)
                    resource_slots={"cpu": 4},
                    environ=None,
                ),
            ),
            _CompletePipelineTestCase(
                id="complete_pipeline_full_priority_chain",
                service_definition_dict={
                    # Root level
                    "environment": {
                        "image": "root-image:latest",
                        "architecture": "amd64",  # Root has architecture
                    },
                    "resource_slots": {
                        "cpu": 4,
                    },
                    # vllm variant (overrides architecture)
                    "vllm": {
                        "environment": {
                            "architecture": "aarch64",  # Variant overrides root
                        },
                    },
                },
                runtime_variant="vllm",
                request=_RequestSpec(
                    image=None,
                    architecture="arm64",  # Request has highest priority
                    resource_slots=None,
                    environ=None,
                ),
                default_architecture="x86_64",
                expected=_ExpectedResult(
                    image="root-image:latest",  # from root
                    # Priority: request (arm64) > vllm (aarch64) > root (amd64) > default (x86_64)
                    architecture="arm64",  # from request (highest)
                    resource_slots={"cpu": 4},
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
        mock_deployment_repository.fetch_service_definition = AsyncMock(
            return_value=test_case.service_definition_dict
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

        # When: Generating revision (complete pipeline with optional default_architecture)
        result = await base_generator.generate_revision(
            draft_revision=requested_revision,
            vfolder_id=vfolder_id,
            model_definition_path="service-definition.toml",
            default_architecture=test_case.default_architecture,
        )

        # Then: Should match expected values
        assert result.image_identifier.canonical == test_case.expected.image
        assert result.image_identifier.architecture == test_case.expected.architecture
        assert result.resource_spec.resource_slots == test_case.expected.resource_slots
        assert result.execution.environ == test_case.expected.environ


class TestDefinitionFileRequirement:
    """
    Test that model definition is only required for CUSTOM runtime variant.
    """

    @pytest.fixture
    def mock_deployment_repository(self) -> MagicMock:
        return MagicMock(spec=DeploymentRepository)

    @pytest.fixture
    def base_generator(self, mock_deployment_repository: MagicMock) -> BaseRevisionGenerator:
        return BaseRevisionGenerator(mock_deployment_repository)

    @pytest.fixture
    def vfolder_id(self) -> UUID:
        return uuid4()

    @pytest.fixture
    def custom_generator(self, mock_deployment_repository: MagicMock):
        return CustomRevisionGenerator(mock_deployment_repository)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "runtime_variant",
        [
            RuntimeVariant.VLLM,
            RuntimeVariant.NIM,
            RuntimeVariant.HUGGINGFACE_TGI,
            RuntimeVariant.SGLANG,
            RuntimeVariant.MODULAR_MAX,
            RuntimeVariant.CMD,
        ],
        ids=lambda v: v.value,
    )
    async def test_non_custom_variants_should_not_require_model_definition(
        self,
        runtime_variant: RuntimeVariant,
        base_generator: BaseRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        """
        Test that non-CUSTOM runtime variants do NOT require model-definition.yaml
        """
        # Given: Only service definition exists (no model definition)
        mock_deployment_repository.fetch_service_definition = AsyncMock(
            return_value={
                "environment": {
                    "image": "test-image:latest",
                    "architecture": "x86_64",
                },
                "resource_slots": {
                    "cpu": 4,
                    "mem": "8gb",
                },
            }
        )

        # When: Generating revision (should NOT call fetch_model_definition)
        result = await base_generator.generate_revision(
            draft_revision=ModelRevisionSpecDraft(
                image_identifier=ImageIdentifierDraft(
                    canonical="request-image:latest",
                    architecture="aarch64",
                ),
                resource_spec=ResourceSpecDraft(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                    resource_slots={"cpu": 2, "mem": "4gb"},
                    resource_opts=None,
                ),
                mounts=MountMetadata(
                    model_vfolder_id=vfolder_id,
                    model_mount_destination="/models",
                    model_definition_path=None,
                    extra_mounts=[],
                ),
                execution=ExecutionSpec(
                    runtime_variant=runtime_variant,
                    startup_command="python -m test",
                    bootstrap_script=None,
                    environ=None,
                ),
            ),
            vfolder_id=vfolder_id,
            model_definition_path=None,
        )

        # Then: Should succeed without requiring model definition
        assert result is not None
        # Then: Should have called fetch_service_definition (not fetch_model_definition)
        mock_deployment_repository.fetch_service_definition.assert_called_once_with(vfolder_id)

    @pytest.mark.asyncio
    async def test_non_custom_variants_work_without_service_definition(
        self,
        base_generator: BaseRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        """
        Test that non-CUSTOM variants work even when service definition is missing.
        Service definition is optional for all variants.
        """
        # Given: No service definition at all
        mock_deployment_repository.fetch_service_definition = AsyncMock(return_value=None)

        # And: API request provides all required fields
        draft_revision = ModelRevisionSpecDraft(
            image_identifier=ImageIdentifierDraft(
                canonical="request-image:latest",
                architecture="x86_64",
            ),
            resource_spec=ResourceSpecDraft(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots={"cpu": 4, "mem": "8gb"},
                resource_opts=None,
            ),
            mounts=MountMetadata(
                model_vfolder_id=vfolder_id,
                model_mount_destination="/models",
                model_definition_path=None,
                extra_mounts=[],
            ),
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant.VLLM,
                startup_command="python -m vllm",
                bootstrap_script=None,
                environ={"MY_VAR": "value"},
            ),
        )

        # When: Generating revision
        result = await base_generator.generate_revision(
            draft_revision=draft_revision,
            vfolder_id=vfolder_id,
            model_definition_path=None,
        )

        # Then: Should succeed using only API request values
        assert result is not None

    @pytest.mark.asyncio
    async def test_custom_variant_requires_model_definition_success(
        self,
        custom_generator: CustomRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        """
        Test that CUSTOM variant requires and validates model definition (success case).
        """
        # Given: Valid model definition
        valid_model_definition = {
            "models": [
                {
                    "name": "test-model",
                    "model-path": "/models/test-model",
                }
            ]
        }
        mock_deployment_repository.fetch_model_definition = AsyncMock(
            return_value=valid_model_definition
        )

        # And: CUSTOM variant revision (already converted to ModelRevisionSpec)
        revision = ModelRevisionSpec(
            image_identifier=ImageIdentifier(
                canonical="custom-image:latest",
                architecture="x86_64",
            ),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots={"cpu": 4, "mem": "8gb"},
                resource_opts=None,
            ),
            mounts=MountMetadata(
                model_vfolder_id=vfolder_id,
                model_mount_destination="/models",
                model_definition_path=None,
                extra_mounts=[],
            ),
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant.CUSTOM,
                startup_command="python app.py",
                bootstrap_script=None,
                environ=None,
            ),
        )

        # When: Validating revision (should call fetch_model_definition)
        await custom_generator.validate_revision(revision)

        # Then: Should call fetch_model_definition (not fetch_service_definition)
        mock_deployment_repository.fetch_model_definition.assert_called_once_with(
            vfolder_id=vfolder_id,
            model_definition_path=None,
        )

    @pytest.mark.asyncio
    async def test_custom_variant_requires_model_definition_failure_not_found(
        self,
        custom_generator: CustomRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        """
        Test that CUSTOM variant fails when model definition file is NOT FOUND.

        This is the critical failure case: CUSTOM variant MUST have model-definition.yaml,
        unlike non-CUSTOM variants which can work without it.
        """
        # Given: Model definition file does not exist
        mock_deployment_repository.fetch_model_definition = AsyncMock(
            side_effect=DefinitionFileNotFound
        )

        # And: CUSTOM variant revision
        revision = ModelRevisionSpec(
            image_identifier=ImageIdentifier(
                canonical="custom-image:latest",
                architecture="x86_64",
            ),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots={"cpu": 4, "mem": "8gb"},
                resource_opts=None,
            ),
            mounts=MountMetadata(
                model_vfolder_id=vfolder_id,
                model_mount_destination="/models",
                model_definition_path=None,
                extra_mounts=[],
            ),
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant.CUSTOM,
                startup_command="python app.py",
                bootstrap_script=None,
                environ=None,
            ),
        )

        # When/Then: Should raise DefinitionFileNotFound
        with pytest.raises(DefinitionFileNotFound):
            await custom_generator.validate_revision(revision)

        # And: Should have attempted to call fetch_model_definition
        mock_deployment_repository.fetch_model_definition.assert_called_once_with(
            vfolder_id=vfolder_id,
            model_definition_path=None,
        )

    @pytest.mark.asyncio
    async def test_custom_variant_requires_valid_model_definition_schema(
        self,
        custom_generator: CustomRevisionGenerator,
        mock_deployment_repository: MagicMock,
        vfolder_id: UUID,
    ) -> None:
        """
        Test that CUSTOM variant rejects INVALID model definition schema.
        """
        # Given: Invalid model definition (wrong type for models field)
        invalid_model_definition = {
            "models": "should_be_a_list_not_a_string",  # Invalid type
        }
        mock_deployment_repository.fetch_model_definition = AsyncMock(
            return_value=invalid_model_definition
        )

        # And: CUSTOM variant revision
        revision = ModelRevisionSpec(
            image_identifier=ImageIdentifier(
                canonical="custom-image:latest",
                architecture="x86_64",
            ),
            resource_spec=ResourceSpec(
                cluster_mode=ClusterMode.SINGLE_NODE,
                cluster_size=1,
                resource_slots={"cpu": 4, "mem": "8gb"},
                resource_opts=None,
            ),
            mounts=MountMetadata(
                model_vfolder_id=vfolder_id,
                model_mount_destination="/models",
                model_definition_path=None,
                extra_mounts=[],
            ),
            execution=ExecutionSpec(
                runtime_variant=RuntimeVariant.CUSTOM,
                startup_command="python app.py",
                bootstrap_script=None,
                environ=None,
            ),
        )

        # When/Then: Should raise InvalidAPIParameters due to invalid schema
        with pytest.raises(InvalidAPIParameters) as exc_info:
            await custom_generator.validate_revision(revision)

        assert "Invalid model definition for CUSTOM variant" in str(exc_info.value)

        # And: Should have called fetch_model_definition
        mock_deployment_repository.fetch_model_definition.assert_called_once_with(
            vfolder_id=vfolder_id,
            model_definition_path=None,
        )
