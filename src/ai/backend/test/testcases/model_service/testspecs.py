import textwrap

from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.model_service.endpoint import (
    EndpointTemplate,
    PublicEndpointTemplate,
)
from ai.backend.test.templates.model_service.jwt_token import ModelServiceTokenTemplate
from ai.backend.test.testcases.model_service.health_check import (
    EndpointHealthCheck,
    EndpointHealthCheckWithToken,
)
from ai.backend.test.testcases.model_service.replicas_scale_successfully import (
    ReplicasScaleSuccessfully,
)
from ai.backend.test.testcases.model_service.scale_failure_too_many_sessions import (
    ReplicasScaleFailureTooManySessions,
)
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.tester.dependency import ClusterDep

from ...templates.template import BasicTestTemplate

SINGLE_NODE_SINGLE_CONTAINER_MODEL_SERVICE_TEST_SPECS = {
    "single_node_single_container_creation_endpoint_success": TestSpec(
        name="single_node_single_container_creation_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is not available without generating JWT token.
            3. Clean up the endpoint after verification.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.MODEL_SERVICE,
            TestTag.SESSION,
            TestTag.SINGLE_NODE_SINGLE_CONTAINER,
        },
        # Endpoint health check failure is expected.
        template=BasicTestTemplate(
            EndpointHealthCheck(expected_status_codes={400, 401})
        ).with_wrappers(KeypairAuthTemplate, EndpointTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ]
        },
    ),
    "single_node_single_container_creation_public_endpoint_success": TestSpec(
        name="single_node_single_container_creation_public_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is created and available.
            3. Clean up the endpoint after verification.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.MODEL_SERVICE,
            TestTag.SESSION,
            TestTag.SINGLE_NODE_SINGLE_CONTAINER,
        },
        template=BasicTestTemplate(EndpointHealthCheck(expected_status_codes={200})).with_wrappers(
            KeypairAuthTemplate, PublicEndpointTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ]
        },
    ),
    "single_node_single_container_creation_private_endpoint_success": TestSpec(
        name="single_node_single_container_creation_private_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is created and available.
            3. Clean up the endpoint after verification.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.MODEL_SERVICE,
            TestTag.SESSION,
            TestTag.SINGLE_NODE_SINGLE_CONTAINER,
        },
        # Endpoint health check success is expected since we're inject JWT token into the request.
        template=BasicTestTemplate(
            EndpointHealthCheckWithToken(expected_status_codes={200})
        ).with_wrappers(KeypairAuthTemplate, EndpointTemplate, ModelServiceTokenTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ]
        },
    ),
    "replicas_successfully_scale": TestSpec(
        name="replicas_successfully_scale",
        description=textwrap.dedent("""\
            Test for successful scaling of replicas in an endpoint.
            This test verifies that the number of replicas can be successfully scaled.
            The test will:
            1. Create an endpoint with a specified number of replicas.
            2. Scale up the replicas and verify the change.
            3. Scale down the replicas and verify the change.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.MODEL_SERVICE, TestTag.SESSION},
        template=BasicTestTemplate(ReplicasScaleSuccessfully()).with_wrappers(
            KeypairAuthTemplate, EndpointTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=3,
                ),
                ClusterDep(
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
    "replicas_scale_failure_too_many_sessions": TestSpec(
        name="replicas_scale_failure_too_many_sessions",
        description=textwrap.dedent("""\
            Test for failure when trying to scale replicas beyond the allowed limit.
            This test verifies that scaling replicas beyond the allowed limit raises an error.
            The test will:
            1. Create an endpoint with a specified number of replicas.
            2. Attempt to scale up the replicas beyond the allowed limit set in user resource policy and verify the error.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.MODEL_SERVICE, TestTag.SESSION},
        template=BasicTestTemplate(ReplicasScaleFailureTooManySessions()).with_wrappers(
            KeypairAuthTemplate, EndpointTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=3,
                ),
                ClusterDep(
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
}

SINGLE_NODE_MULTI_CONTAINER_MODEL_SERVICE_TEST_SPECS = {
    "single_node_multi_container_creation_endpoint_success": TestSpec(
        name="single_node_multi_container_creation_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is not available without generating JWT token.
            3. Clean up the endpoint after verification.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.MODEL_SERVICE,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        # Endpoint health check failure is expected.
        template=BasicTestTemplate(
            EndpointHealthCheck(expected_status_codes={400, 401})
        ).with_wrappers(KeypairAuthTemplate, EndpointTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
    "single_node_multi_container_creation_public_endpoint_success": TestSpec(
        name="single_node_multi_container_creation_public_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is created and available.
            3. Clean up the endpoint after verification.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.MODEL_SERVICE,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(EndpointHealthCheck(expected_status_codes={200})).with_wrappers(
            KeypairAuthTemplate, PublicEndpointTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
    "single_node_multi_container_creation_private_endpoint_success": TestSpec(
        name="single_node_multi_container_creation_private_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is created and available.
            3. Clean up the endpoint after verification.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.MODEL_SERVICE,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        # Endpoint health check success is expected since we're inject JWT token into the request.
        template=BasicTestTemplate(
            EndpointHealthCheckWithToken(expected_status_codes={200})
        ).with_wrappers(KeypairAuthTemplate, EndpointTemplate, ModelServiceTokenTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
}

MULTI_NODE_MULTI_CONTAINER_MODEL_SERVICE_TEST_SPECS = {
    "multi_node_multi_container_creation_endpoint_success": TestSpec(
        name="multi_node_multi_container_creation_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is not available without generating JWT token.
            3. Clean up the endpoint after verification.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.MODEL_SERVICE,
            TestTag.SESSION,
            TestTag.REQUIRED_MULTI_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        # Endpoint health check failure is expected.
        template=BasicTestTemplate(
            EndpointHealthCheck(expected_status_codes={400, 401})
        ).with_wrappers(KeypairAuthTemplate, EndpointTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
    "multi_node_multi_container_creation_public_endpoint_success": TestSpec(
        name="multi_node_multi_container_creation_public_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is created and available.
            3. Clean up the endpoint after verification.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.MODEL_SERVICE,
            TestTag.SESSION,
            TestTag.REQUIRED_MULTI_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(EndpointHealthCheck(expected_status_codes={200})).with_wrappers(
            KeypairAuthTemplate, PublicEndpointTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
    "multi_node_multi_container_creation_private_endpoint_success": TestSpec(
        name="multi_node_multi_container_creation_private_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is created and available.
            3. Clean up the endpoint after verification.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.MODEL_SERVICE,
            TestTag.SESSION,
            TestTag.REQUIRED_MULTI_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        # Endpoint health check success is expected since we're inject JWT token into the request.
        template=BasicTestTemplate(
            EndpointHealthCheckWithToken(expected_status_codes={200})
        ).with_wrappers(KeypairAuthTemplate, EndpointTemplate, ModelServiceTokenTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
}

MODEL_SERVICE_TEST_SPECS = {
    **SINGLE_NODE_SINGLE_CONTAINER_MODEL_SERVICE_TEST_SPECS,
    **SINGLE_NODE_MULTI_CONTAINER_MODEL_SERVICE_TEST_SPECS,
    **MULTI_NODE_MULTI_CONTAINER_MODEL_SERVICE_TEST_SPECS,
}
