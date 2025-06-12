import textwrap

from ai.backend.test.templates.session.batch_session import BatchSessionTemplate
from ai.backend.test.templates.session.interactive_session import InteractiveSessionTemplate
from ai.backend.test.testcases.session.session_creation_failure_low_resources import (
    SessionCreationFailureLowResources,
)
from ai.backend.test.testcases.session.session_creation_failure_too_many_container import (
    SessionCreationFailureTooManyContainer,
)

from ...templates.template import BasicTestTemplate, NopTestCode
from ..testcases import TestSpec, TestTag

SESSION_TEST_SPECS = {
    "single_node_single_container_batch_session": TestSpec(
        name="single_node_single_container_batch_session",
        description=textwrap.dedent("""\
            Test for creating a single-node, single-container batch session.
            This test verifies that a session can be created with a single node and a single container, and that it transitions through the expected lifecycle events.
            The test will:
            1. Create a batch session with the specified image and resources.
            2. Listen for lifecycle events and verify that the session transitions through the expected states.
            3. Assert that the session is terminated after completion.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BatchSessionTemplate(BasicTestTemplate(NopTestCode())),
    ),
    # "single_node_multi_container_batch_session": TestSpec(
    #     name="single_node_multi_container_batch_session",
    #     description=textwrap.dedent("""\
    #         Test for creating a single-node, multi-container batch session.
    #         This test verifies that a session can be created with a single node and multiple containers, and that it transitions through the expected lifecycle events.
    #         The test will:
    #         1. Create a batch session with the specified image and resources.
    #         2. Listen for lifecycle events and verify that the session transitions through the expected states.
    #         3. Assert that the session is terminated after completion.
    #     """),
    #     tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
    #     template=BatchSessionTemplate(BasicTestTemplate(NopTestCode())),
    # ),
    # "multi_node_multi_container_batch_session": TestSpec(
    #     name="multi_node_multi_container_batch_session",
    #     description=textwrap.dedent("""\
    #         Test for creating a multi-node, multi-container batch session.
    #         This test verifies that a session can be created with multiple nodes and multiple containers, and that it transitions through the expected lifecycle events.
    #         The test will:
    #         1. Create a batch session with the specified image and resources.
    #         2. Listen for lifecycle events and verify that the session transitions through the expected states.
    #         3. Assert that the session is terminated after completion.
    #     """),
    #     tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
    #     template=BatchSessionTemplate(BasicTestTemplate(NopTestCode())),
    # ),
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
        template=InteractiveSessionTemplate(BasicTestTemplate(NopTestCode())),
    ),
    "create_session_failure_due_to_low_resources": TestSpec(
        name="create_session_failure_due_to_low_resources",
        description=textwrap.dedent("""\
            Test for creating a session with too low resources.
            This test verifies that a session creation fails when the specified resources are insufficient to run the image.
            The test will:
            1. Attempt to create a session with the specified image and insufficient resources.
            2. Assert that the session creation fails with an appropriate error message.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(SessionCreationFailureLowResources()),
    ),
    "create_session_failure_due_to_too_many_container_count": TestSpec(
        name="create_session_failure_due_to_too_many_container_count",
        description=textwrap.dedent("""\
            Test for creating a session with too many containers.
            This test verifies that a session creation fails when the specified container count exceeds the limit.
            The test will:
            1. Attempt to create a session with the specified image and too many containers.
            2. Assert that the session creation fails with an appropriate error message.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(SessionCreationFailureTooManyContainer()),
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
