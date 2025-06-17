import textwrap
from pathlib import Path

from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.context import ContextName
from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.session.batch_session import BatchSessionTemplate
from ai.backend.test.templates.session.dependent_session import DependentSessionTemplate
from ai.backend.test.templates.session.interactive_session import (
    InteractiveSessionTemplate,
    InteractiveSessionWithBootstrapScriptTemplate,
)
from ai.backend.test.templates.session.session_template import (
    BatchSessionFromTemplateTemplate,
    InteractiveSessionFromTemplateTemplate,
    SessionTemplateTemplate,
)
from ai.backend.test.testcases.session.container_log_retriever import TestContainerLogRetriever
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
from ai.backend.test.testcases.session.execution import (
    InteractiveSessionExecuteCodeFailureWrongCommand,
    InteractiveSessionExecuteCodeSuccess,
)
from ai.backend.test.testcases.session.graph_dependency_retriever import DependencyGraphRetriever
from ai.backend.test.testcases.session.filecheck import FileExistenceCheck
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.tester.dependency import (
    BootstrapScriptDep,
    ClusterDep,
    CodeExecutionDep,
)

from ...templates.template import BasicTestTemplate, NopTestCode

BATCH_SESSION_TEST_SPECS = {
    "creation_batch_session_success": TestSpec(
        name="creation_batch_session_success",
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
    "creation_interactive_session_success_with_bootstrap_script": TestSpec(
        name="creation_interactive_session_success_with_bootstrap_script",
        description=textwrap.dedent("""\
            Test for creating a single-node, single-container session.
            This test verifies that a session can be created with a single node and a single container, and that it transitions through the expected lifecycle events.
            The test will:
            1. Create a session with the specified image and resources.
            2. Execute a bootstrap script to create a directory in the session.
            3. Check that the directory was created successfully.
            4. Assert that the session is successfully created and running.
            5. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(
            FileExistenceCheck(path=Path("."), checklist=["test-abc"])
        ).with_wrappers(KeypairAuthTemplate, InteractiveSessionWithBootstrapScriptTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ],
            ContextName.BOOTSTRAP_SCRIPT: [
                BootstrapScriptDep(
                    bootstrap_script="mkdir -p /home/work/test-abc",
                )
            ],
        },
    ),
    "execution_command_on_interactive_session_success": TestSpec(
        name="execution_command_on_interactive_session_success",
        description=textwrap.dedent("""\
            Test for executing code in an interactive session.
            This test verifies that code can be executed in an interactive session, and that the session transitions through the expected lifecycle events.
            The test will:
            1. Create an interactive session with the specified image and resources.
            2. Execute a command in the session and verify the output.
            3. Assert that the session is running after execution.
            4. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(InteractiveSessionExecuteCodeSuccess()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
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
            ],
            ContextName.CODE_EXECUTION: [
                CodeExecutionDep(code='print("Hello, world!")', expected_result="Hello, world!\n"),
                CodeExecutionDep(code="1 + 1", expected_result="2"),
            ],
        },
    ),
    "execution_command_on_interactive_session_failure_wrong_command": TestSpec(
        name="execution_command_on_interactive_session_failure_wrong_command",
        description=textwrap.dedent("""\
            Test for executing code in an interactive session.
            This test verifies that code can be executed in an interactive session, and that the session transitions through the expected lifecycle events.
            The test will:
            1. Create an interactive session with the specified image and resources.
            2. Execute a command in the session and verify the output.
            3. Assert that the session is running after execution.
            4. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(
            InteractiveSessionExecuteCodeFailureWrongCommand()
        ).with_wrappers(KeypairAuthTemplate, InteractiveSessionTemplate),
        parametrizes={
            ContextName.CLUSTER_CONFIG: [
                ClusterDep(
                    cluster_mode=ClusterMode.SINGLE_NODE,
                    cluster_size=1,
                ),
            ],
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
    "creation_batch_session_success_from_template": TestSpec(
        name="creation_batch_session_success_from_template",
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
            ],
        },
    ),
}

SESSION_INFO_RETRIEVER_TEST_SPECS = {
    "session_container_log_retriever": TestSpec(
        name="session_container_log_retriever",
        description=textwrap.dedent("""\
        Test for retrieving logs from a session's kernel(container).
        This test ensures that logs can be fetched from a running session's kernel(container).
        The test will:
        1. Create a session and start a kernel(container).
        2. Perform actions that generate logs in the kernel(container).
        3. Retrieve the logs from the kernel(container).
        4. Assert that the retrieved logs contain the expected output.
        5. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(testcode=TestContainerLogRetriever()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
        ),
    ),
    "session_dependency_graph_retriever": TestSpec(
        name="session_dependency_graph_retriever",
        description=textwrap.dedent("""
            Retrieve and validate the dependency graph of a compute session,
            ensuring the session name matches and the dependency structure is present.
        """),
        tags={TestTag.SESSION, TestTag.MANAGER},
        template=BasicTestTemplate(testcode=DependencyGraphRetriever()).with_wrappers(
            KeypairAuthTemplate, BatchSessionTemplate, DependentSessionTemplate
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
            ],
        },
    ),
}


SESSION_TEST_SPECS = {
    **BATCH_SESSION_TEST_SPECS,
    **INTERACTIVE_SESSION_TEST_SPECS,
    **SESSION_TEMPLATE_TEST_SPECS,
    **SESSION_INFO_RETRIEVER_TEST_SPECS,
}
