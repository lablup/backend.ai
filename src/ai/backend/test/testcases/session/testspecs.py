import textwrap

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.testcases.session.creation_failure_command_timeout import (
    BatchSessionCreationFailureTimeout,
)
from ai.backend.test.testcases.session.creation_failure_low_resources import (
    SessionCreationFailureLowResources,
)
from ai.backend.test.testcases.session.creation_failure_schedule_timeout import (
    InteractiveSessionCreationFailureScheduleTimeout,
)
from ai.backend.test.testcases.session.creation_failure_too_many_container import (
    SessionCreationFailureTooManyContainer,
)
from ai.backend.test.testcases.session.creation_failure_wrong_command import (
    BatchSessionCreationFailureWrongCommand,
)
from ai.backend.test.testcases.session.multi_node_multi_container.testspecs import (
    MULTI_NODE_MULTI_CONTAINER_SESSION_TEST_SPECS,
)
from ai.backend.test.testcases.session.single_node_multi_container.testspecs import (
    SINGLE_NODE_MULTI_CONTAINER_SESSION_TEST_SPECS,
)
from ai.backend.test.testcases.session.single_node_single_container.testspecs import (
    SINGLE_NODE_SIGNLE_CONTAINER_SESSION_TEST_SPECS,
)
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

BATCH_SESSION_FAILURE_TEST_SPECS = {
    "creation_batch_session_failure_wrong_command": TestSpec(
        name="creation_batch_session_failure_wrong_command",
        description=textwrap.dedent("""\
            Test for creating a batch session with an invalid startup command.
            This test verifies that a batch session creation fails when the startup command is invalid.
            The test will:
            1. Attempt to create a batch session with the specified image and an invalid startup command.
            2. Assert that the session creation fails with an appropriate error message.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(BatchSessionCreationFailureWrongCommand()).with_wrappers(
            KeypairAuthTemplate
        ),
    ),
    "creation_batch_session_failure_command_timeout": TestSpec(
        name="creation_batch_session_failure_command_timeout",
        description=textwrap.dedent("""\
            Test for creating a batch session with an invalid startup command.
            This test verifies that a batch session creation fails when the startup command is invalid.
            The test will:
            1. Attempt to create a batch session with the specified image and an invalid startup command.
            2. Assert that the session creation fails with an appropriate error message.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(BatchSessionCreationFailureTimeout()).with_wrappers(
            KeypairAuthTemplate
        ),
    ),
}

INTERACTIVE_SESSION_FAILURE_TEST_SPECS = {
    "creation_interactive_session_failure_low_resources": TestSpec(
        name="creation_interactive_session_failure_low_resources",
        description=textwrap.dedent("""\
            Test for creating a session with too low resources.
            This test verifies that a session creation fails when the specified resources are insufficient to run the image.
            The test will:
            1. Attempt to create a session with the specified image and insufficient resources.
            2. Assert that the session creation fails with an appropriate error message.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(SessionCreationFailureLowResources()).with_wrappers(
            KeypairAuthTemplate
        ),
    ),
    "creation_interactive_session_failure_too_many_container_count": TestSpec(
        name="creation_interactive_session_failure_too_many_container_count",
        description=textwrap.dedent("""\
            Test for creating a session with too many containers.
            This test verifies that a session creation fails when the specified container count exceeds the limit.
            The test will:
            1. Attempt to create a session with the specified image and too many containers.
            2. Assert that the session creation fails with an appropriate error message.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(SessionCreationFailureTooManyContainer()).with_wrappers(
            KeypairAuthTemplate
        ),
    ),
    "creation_interactive_session_failure_schedule_timeout": TestSpec(
        name="creation_interactive_session_failure_schedule_timeout",
        description=textwrap.dedent("""\
            Test for creating a session with too many containers.
            This test verifies that a session creation fails when the specified container count exceeds the limit.
            The test will:
            1. Attempt to create a session with the specified image and too many containers.
            2. Assert that the session creation fails with an appropriate error message.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(
            InteractiveSessionCreationFailureScheduleTimeout()
        ).with_wrappers(KeypairAuthTemplate),
    ),
}


SESSION_TEST_SPECS = {
    **SINGLE_NODE_SIGNLE_CONTAINER_SESSION_TEST_SPECS,
    **SINGLE_NODE_MULTI_CONTAINER_SESSION_TEST_SPECS,
    **MULTI_NODE_MULTI_CONTAINER_SESSION_TEST_SPECS,
    **BATCH_SESSION_FAILURE_TEST_SPECS,
    **INTERACTIVE_SESSION_FAILURE_TEST_SPECS,
}
