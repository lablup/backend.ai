"""
Tests for apply_service_definition_overrides method in ModelServingService.
"""

from dataclasses import dataclass
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest

from ai.backend.common.types import RuntimeVariant
from ai.backend.manager.services.model_serving.services.model_serving import (
    ApiRequestedServiceConfig,
    ModelServingService,
)


@dataclass
class _ServiceDefinitionTestCase:
    """Test case for apply_service_definition_overrides."""

    id: str
    service_definition_dict: dict[str, Any]
    runtime_variant: RuntimeVariant
    api_request: ApiRequestedServiceConfig
    expected_image: Optional[str]
    expected_architecture: Optional[str]
    expected_resource_slots: Optional[dict[str, Any]]
    expected_environ: Optional[dict[str, str]]


class TestApplyServiceDefinitionOverrides:
    """Test apply_service_definition_overrides method - 3-stage merge logic."""

    @pytest.fixture
    def model_serving_service(self) -> ModelServingService:
        """Create ModelServingService with minimal mocks for testing."""
        return ModelServingService(
            agent_registry=MagicMock(),
            background_task_manager=MagicMock(),
            event_dispatcher=MagicMock(),
            storage_manager=MagicMock(),
            config_provider=MagicMock(),
            valkey_live=MagicMock(),
            repository=MagicMock(),
            admin_repository=MagicMock(),
            deployment_controller=MagicMock(),
        )

    @pytest.mark.parametrize(
        "test_case",
        [
            _ServiceDefinitionTestCase(
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
                runtime_variant=RuntimeVariant.VLLM,
                api_request=ApiRequestedServiceConfig(
                    image=None,
                    architecture=None,
                    resource_slots=None,
                    environ=None,
                ),
                expected_image="default-image:latest",
                expected_architecture="x86_64",
                expected_resource_slots={"cpu": 4, "mem": "16gb"},
                expected_environ={"MY_VAR": "default"},
            ),
            _ServiceDefinitionTestCase(
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
                runtime_variant=RuntimeVariant.VLLM,
                api_request=ApiRequestedServiceConfig(
                    image=None,
                    architecture=None,
                    resource_slots=None,
                    environ=None,
                ),
                expected_image="vllm-image:latest",
                expected_architecture="aarch64",
                expected_resource_slots={"cpu": 8, "mem": "32gb"},
                expected_environ={"VLLM_VAR": "vllm-value"},
            ),
            _ServiceDefinitionTestCase(
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
                    # Variant section (overrides only image and cpu, adds VLLM_SPECIFIC)
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
                runtime_variant=RuntimeVariant.VLLM,
                api_request=ApiRequestedServiceConfig(
                    image=None,
                    architecture=None,
                    resource_slots=None,
                    environ=None,
                ),
                expected_image="vllm-optimized:latest",  # from vllm
                expected_architecture="x86_64",  # from root
                expected_resource_slots={"cpu": 8, "mem": "16gb"},  # cpu from vllm, mem from root
                expected_environ={
                    "MY_VAR": "default",
                    "VLLM_SPECIFIC": "true",
                },  # merged
            ),
            _ServiceDefinitionTestCase(
                id="api_request_overrides_all",
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
                runtime_variant=RuntimeVariant.VLLM,
                api_request=ApiRequestedServiceConfig(
                    image="request-image:latest",
                    architecture="aarch64",
                    resource_slots={"cpu": 2, "mem": "8gb"},
                    environ={"REQUEST_VAR": "request-value"},
                ),
                expected_image="request-image:latest",  # from request
                expected_architecture="aarch64",  # from request
                expected_resource_slots={
                    "cpu": 2,
                    "mem": "8gb",
                },  # from request (overrides all)
                expected_environ={
                    "MY_VAR": "default",
                    "VLLM_VAR": "vllm-value",
                    "REQUEST_VAR": "request-value",
                },  # all merged
            ),
            _ServiceDefinitionTestCase(
                id="api_request_partial_override",
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
                        "SERVICE_VAR": "service-value",
                    },
                },
                runtime_variant=RuntimeVariant.VLLM,
                api_request=ApiRequestedServiceConfig(
                    image="request-image:latest",  # Override image
                    architecture=None,  # Use service definition
                    resource_slots={"cpu": 2},  # Override cpu only
                    environ={"REQUEST_VAR": "request-value"},  # Merge with service
                ),
                expected_image="request-image:latest",  # from request
                expected_architecture="x86_64",  # from service definition
                expected_resource_slots={
                    "cpu": 2,
                    "mem": "16gb",
                },  # cpu from request, mem from service
                expected_environ={
                    "SERVICE_VAR": "service-value",
                    "REQUEST_VAR": "request-value",
                },  # merged
            ),
            _ServiceDefinitionTestCase(
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
                            "image": "sglang-image:latest",
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
                runtime_variant=RuntimeVariant.VLLM,
                api_request=ApiRequestedServiceConfig(
                    image=None,
                    architecture=None,
                    resource_slots=None,
                    environ=None,
                ),
                expected_image="default-image:latest",  # from root
                expected_architecture="x86_64",  # from root
                expected_resource_slots={"cpu": 8, "mem": "16gb"},  # cpu from vllm, mem from root
                expected_environ=None,
            ),
            _ServiceDefinitionTestCase(
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
                runtime_variant=RuntimeVariant.VLLM,
                api_request=ApiRequestedServiceConfig(
                    image="request-image:latest",  # Override vllm's image
                    architecture=None,  # Use from service definition
                    resource_slots={"cpu": 2},  # Override vllm's cpu again
                    environ={"REQUEST_VAR": "request-value"},
                ),
                expected_image="request-image:latest",  # from request
                expected_architecture="x86_64",  # from root
                expected_resource_slots={
                    "cpu": 2,
                    "mem": "16gb",
                },  # cpu from request, mem from root
                expected_environ={
                    "ROOT_VAR": "root-value",
                    "VLLM_VAR": "vllm-value",
                    "REQUEST_VAR": "request-value",
                },  # all merged
            ),
            _ServiceDefinitionTestCase(
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
                runtime_variant=RuntimeVariant.VLLM,
                api_request=ApiRequestedServiceConfig(
                    image="request-image:latest",  # Should have highest priority
                    architecture="aarch64",  # Override root's x86_64
                    resource_slots={"cpu": 2},  # Override vllm's 8
                    environ=None,
                ),
                expected_image="request-image:latest",  # request > vllm > root
                expected_architecture="aarch64",  # request > root
                expected_resource_slots={"cpu": 2},  # request > vllm > root
                expected_environ=None,
            ),
        ],
        ids=lambda tc: tc.id,
    )
    @pytest.mark.asyncio
    async def test_apply_service_definition_overrides(
        self,
        test_case: _ServiceDefinitionTestCase,
        model_serving_service: ModelServingService,
    ) -> None:
        """Test apply_service_definition_overrides with various override scenarios."""
        # When: Applying service definition overrides
        result = await model_serving_service.apply_service_definition_overrides(
            service_definition=test_case.service_definition_dict,
            runtime_variant=test_case.runtime_variant,
            user_requested_variables=test_case.api_request,
        )

        # Then: Should match expected values
        assert result.image == test_case.expected_image
        assert result.architecture == test_case.expected_architecture
        assert result.resource_slots == test_case.expected_resource_slots
        assert result.environ == test_case.expected_environ
