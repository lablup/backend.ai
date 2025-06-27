import textwrap

from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.model_service.auto_scaling_rule import AutoScalingRuleTemplate
from ai.backend.test.templates.model_service.endpoint import (
    EndpointTemplate,
    PublicEndpointTemplate,
)
from ai.backend.test.templates.model_service.jwt_token import ModelServiceTokenTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.testcases.config import STANDARD_CLUSTER_CONFIGS
from ai.backend.test.testcases.model_service.health_check import (
    EndpointHealthCheck,
    EndpointHealthCheckWithToken,
)
from ai.backend.test.testcases.model_service.scale_by_auto_scaling_rule import (
    ScaleByAutoScalingRules,
)
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

MODEL_SERVICE_TEST_SPECS = {
    "creation_endpoint_success": TestSpec(
        name="creation_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is not available without generating JWT token.
            3. Clean up the endpoint after verification.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.MODEL_SERVICE, TestTag.SESSION},
        # Endpoint health check failure is expected.
        template=BasicTestTemplate(
            EndpointHealthCheck(expected_status_codes={400, 401})
        ).with_wrappers(KeypairAuthTemplate, EndpointTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: STANDARD_CLUSTER_CONFIGS,
        },
    ),
    "creation_public_endpoint_success": TestSpec(
        name="creation_public_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is created and available.
            3. Clean up the endpoint after verification.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.MODEL_SERVICE, TestTag.SESSION},
        template=BasicTestTemplate(EndpointHealthCheck(expected_status_codes={200})).with_wrappers(
            KeypairAuthTemplate, PublicEndpointTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: STANDARD_CLUSTER_CONFIGS,
        },
    ),
    "creation_private_endpoint_success": TestSpec(
        name="creation_private_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is created and available.
            3. Clean up the endpoint after verification.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.MODEL_SERVICE, TestTag.SESSION},
        # Endpoint health check success is expected since we're inject JWT token into the request.
        template=BasicTestTemplate(
            EndpointHealthCheckWithToken(expected_status_codes={200})
        ).with_wrappers(KeypairAuthTemplate, EndpointTemplate, ModelServiceTokenTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: STANDARD_CLUSTER_CONFIGS,
        },
    ),
    "scale_by_auto_scaling_rule_success": TestSpec(
        name="scale_by_auto_scaling_rule_success",
        description=textwrap.dedent("""\
            Test for successful scaling of a service by auto-scaling rule.
            This test verifies that a service can be scaled successfully using an auto-scaling rule.
            The test will:
            1. Create an auto-scaling rule with specified parameters.
            2. Scale the service using the auto-scaling rule.
            3. Verify that the service is scaled successfully.
            4. Clean up the auto-scaling rule after verification.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.MODEL_SERVICE},
        template=BasicTestTemplate(ScaleByAutoScalingRules()).with_wrappers(
            KeypairAuthTemplate, EndpointTemplate, AutoScalingRuleTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: STANDARD_CLUSTER_CONFIGS,
        },
    ),
}
