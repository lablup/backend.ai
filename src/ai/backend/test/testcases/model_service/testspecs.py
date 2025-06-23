import textwrap

from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.model_service.endpoint import (
    EndpointTemplate,
)
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.tester.dependency import ClusterDep

from ...templates.template import BasicTestTemplate, NopTestCode

MODEL_SERVICE_TEST_SPECS = {
    "creation_endpoint_success": TestSpec(
        name="creation_endpoint_success",
        description=textwrap.dedent("""\
            Test for successful creation of an endpoint.
            This test verifies that an endpoint can be created successfully.
            The test will:
            1. Create an endpoint with a specified name and resources.
            2. Verify that the endpoint is created and available.
            3. Clean up the endpoint after verification.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.MODEL_SERVICE, TestTag.SESSION},
        template=BasicTestTemplate(NopTestCode()).with_wrappers(
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
