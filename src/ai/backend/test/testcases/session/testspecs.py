import textwrap

from ai.backend.test.templates.session.create_session import SessionTemplate

from ...templates.template import BasicTestTemplate, NopTestCode
from ..testcases import TestSpec, TestTag

SESSION_TEST_SPECS = {
    "single_node_single_container_session": TestSpec(
        name="single_node_single_container_session",
        description=textwrap.dedent("""\
            Test for creating a single-node, single-container session.
            This test verifies that a session can be created with a single node and a single container, and that it transitions through the expected lifecycle events.

            The test will:
            1. Create a session with the specified image and resources.
            2. Listen for lifecycle events and verify that the session transitions through the expected states.
            3. Assert that the session is running after creation.
            4. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=SessionTemplate(BasicTestTemplate(NopTestCode())),
    ),
    # "single_node_multi_container_session": TestSpec(
    #     name="single_node_multi_container_session",
    #     description=textwrap.dedent("""\
    #         Test for creating a single-node, multi-container session.
    #         This test verifies that a session can be created with a single node and multiple containers, and that it transitions through the expected lifecycle events.
    #         The test will:
    #         1. Create a session with the specified image and resources.
    #         2. Listen for lifecycle events and verify that the session transitions through the expected states.
    #         3. Assert that the session is running after creation.
    #         4. Destroy the session after the test is complete.
    #     """),
    #     tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
    #     template=SessionTemplate(
    #         BasicTestTemplate(NopTestCode())
    #     ),
    # ),
    # "multi_node_multi_container_session": TestSpec(
    #     name="multi_node_multi_container_session",
    #     description=textwrap.dedent("""\
    #         Test for creating a multi-node, multi-container session.
    #         This test verifies that a session can be created with multiple nodes and multiple containers, and that it transitions through the expected lifecycle events.
    #         The test will:
    #         1. Create a session with the specified image and resources.
    #         2. Listen for lifecycle events and verify that the session transitions through the expected states.
    #         3. Assert that the session is running after creation.
    #         4. Destroy the session after the test is complete.
    #     """),
    #     tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
    #     template=SessionTemplate(
    #         BasicTestTemplate(NopTestCode())
    #     ),
    # ),
}
