import textwrap

from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.model_service.endpoint import EndpointTemplate
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
            1. Attempt to create a batch session with the specified image and an invalid startup command.
            2. Assert that the session creation fails with an appropriate error message.
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
