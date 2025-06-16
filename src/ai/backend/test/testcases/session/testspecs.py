import textwrap

from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.session.batch_session import BatchSessionTemplate
from ai.backend.test.templates.session.interactive_session import InteractiveSessionTemplate
from ai.backend.test.templates.session.session_template import (
    BatchSessionFromTemplateTemplate,
    InteractiveSessionFromTemplateTemplate,
    SessionTemplateTemplate,
)
from ai.backend.test.testcases.session.creation_failure_low_resources import (
    SessionCreationFailureLowResources,
)
from ai.backend.test.testcases.session.creation_failure_too_many_container import (
    SessionCreationFailureTooManyContainer,
)
from ai.backend.test.testcases.session.execution_failure_wrong_command import (
    BatchSessionCreationFailureWrongCommand,
)
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.tester.config import ClusterConfig

from ...templates.template import BasicTestTemplate, NopTestCode

BATCH_SESSION_TEST_SPECS = {
    "execution_batch_session_success": TestSpec(
        name="execution_batch_session_success",
        description=textwrap.dedent("""\
            Test for creating a single-node, single-container batch session.
            This test verifies that a session can be created with a single node and a single container, and that it transitions through the expected lifecycle events.
            The test will:
            1. Create a batch session with the specified image and resources.
            2. Listen for lifecycle events and verify that the session transitions through the expected states.
            3. Assert that the session is terminated after completion.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(NopTestCode()).with_wrappers(
            KeypairAuthTemplate, BatchSessionTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterConfig(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                ClusterConfig(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=3,
                ),
                ClusterConfig(
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
    "execution_batch_session_failure_wrong_command": TestSpec(
        name="execution_batch_session_failure_wrong_command",
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
}

INTERACTIVE_SESSION_TEST_SPECS = {
    "creation_interactive_session_success": TestSpec(
        name="creation_interactive_session_success",
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
        template=BasicTestTemplate(NopTestCode()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterConfig(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                ClusterConfig(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=3,
                ),
                ClusterConfig(
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
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
}

SESSION_TEMPLATE_TEST_SPECS = {
    "creation_interactive_session_success_from_template": TestSpec(
        name="creation_interactive_session_success_from_template",
        description=textwrap.dedent("""\
        Test for creating a session from a template.
        This test verifies that a session can be created from a predefined template, and that it transitions through the expected lifecycle events.
        The test will:
        1. Create a session from the specified template.
        2. Listen for lifecycle events and verify that the session transitions through the expected states.
        3. Assert that the session is running after creation.
        4. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(NopTestCode()).with_wrappers(
            KeypairAuthTemplate, SessionTemplateTemplate, InteractiveSessionFromTemplateTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterConfig(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                ClusterConfig(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=3,
                ),
                ClusterConfig(
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=3,
                ),
            ]
        },
    ),
    "execution_batch_session_success_from_template": TestSpec(
        name="execution_batch_session_success_from_template",
        description=textwrap.dedent("""\
        Test for executing a session from a template.
        This test verifies that a session can be executed from a predefined template, and that it transitions through the expected lifecycle events.
        The test will:
        1. Create a session from the specified template.
        2. Listen for lifecycle events and verify that the session transitions through the expected states.
        3. Assert that the session is terminated after completion.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(NopTestCode()).with_wrappers(
            KeypairAuthTemplate, SessionTemplateTemplate, BatchSessionFromTemplateTemplate
        ),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterConfig(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
                ClusterConfig(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=3,
                ),
                ClusterConfig(
                    cluster_mode=ClusterMode.MULTI_NODE,
                    cluster_size=3,
                ),
            ],
            # ContextName.CREATED_SESSION: [
            #     SessionArgs(
            #         image="ubuntu:latest",
            #         resources={"cpu": 1, "mem": "512MiB"},
            #         startup_command="echo 'Hello, World!'",
            #     )
            # ],
        },
    ),
}


SESSION_TEST_SPECS = {
    **BATCH_SESSION_TEST_SPECS,
    **INTERACTIVE_SESSION_TEST_SPECS,
    **SESSION_TEMPLATE_TEST_SPECS,
}
