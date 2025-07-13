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
from ai.backend.test.templates.session.vfolder_mounted_interactive_session import (
    VFolderMountedInteractiveSessionTemplate,
)
from ai.backend.test.templates.template import BasicTestTemplate, NopTestCode
from ai.backend.test.templates.vfolder.general_vfolder import ProjectVFolderTemplate
from ai.backend.test.testcases.session.commit import (
    InteractiveSessionCommitSuccess,
    InteractiveSessionImagifySuccess,
)
from ai.backend.test.testcases.session.container_log_retriever import TestContainerLogRetriever
from ai.backend.test.testcases.session.execution import (
    InteractiveSessionExecuteCodeFailureWithCustomExitCode,
    InteractiveSessionExecuteCodeFailureWrongCommand,
    InteractiveSessionExecuteCodeSuccess,
)
from ai.backend.test.testcases.session.filecheck import FileExistenceCheck
from ai.backend.test.testcases.session.graph_dependency_retriever import DependencyGraphRetriever
from ai.backend.test.testcases.session.rename_failure_duplicated_name import (
    SessionRenameFailureDuplicatedName,
)
from ai.backend.test.testcases.session.session_rename import TestSessionRename
from ai.backend.test.testcases.session.session_status_history_retriever import (
    SessionStatusHistoryRetriever,
)
from ai.backend.test.testcases.session.vfolder_mount import FileHandlingInMountedVFolderSuccess
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag
from ai.backend.test.tester.dependency import (
    BootstrapScriptDep,
    ClusterDep,
    CodeExecutionDep,
)

CLUSTER_CONFIG_PARAM = {
    ContextName.CLUSTER_CONFIG: [
        ClusterDep(
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=2,
        ),
    ]
}

BATCH_SESSION_TEST_SPECS = {
    "single_node_multi_container_creation_batch_session_success": TestSpec(
        name="single_node_multi_container_creation_batch_session_success",
        description=textwrap.dedent("""\
            Test for creating a single-node, multi-container batch session.
            This test verifies that a session can be created with a single node and multiple containers, and that it transitions through the expected lifecycle events.
            The test will:
            1. Create a batch session with the specified image and resources.
            2. Listen for lifecycle events and verify that the session transitions through the expected states.
            3. Assert that the session is terminated after completion.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(NopTestCode()).with_wrappers(
            KeypairAuthTemplate, BatchSessionTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
}

INTERACTIVE_SESSION_TEST_SPECS = {
    "single_node_multi_container_creation_interactive_session_success": TestSpec(
        name="single_node_multi_container_creation_interactive_session_success",
        description=textwrap.dedent("""\
            Test for creating a single-node, multi-container session.
            This test verifies that a session can be created with a single node and multiple containers, and that it transitions through the expected lifecycle events.
            The test will:
            1. Create a session with the specified image and resources.
            2. Listen for lifecycle events and verify that the session transitions through the expected states.
            3. Assert that the session is running after creation.
            4. Destroy the session after the test is complete.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(NopTestCode()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
    "single_node_multi_container_creation_interactive_session_success_with_bootstrap_script": TestSpec(
        name="single_node_multi_container_creation_interactive_session_success_with_bootstrap_script",
        description=textwrap.dedent("""\
            Test for creating a single-node, multi-container session.
            This test verifies that a session can be created with a single node and multiple containers, and that it transitions through the expected lifecycle events.
            The test will:
            1. Create a session with the specified image and resources.
            2. Execute a bootstrap script to create a directory in the session.
            3. Check that the directory was created successfully.
            4. Assert that the session is successfully created and running.
            5. Destroy the session after the test is complete.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(
            FileExistenceCheck(path=Path("."), checklist=["test-abc"])
        ).with_wrappers(KeypairAuthTemplate, InteractiveSessionWithBootstrapScriptTemplate),
        parametrizes={
            **CLUSTER_CONFIG_PARAM,
            ContextName.BOOTSTRAP_SCRIPT: [
                BootstrapScriptDep(
                    bootstrap_script="mkdir -p /home/work/test-abc",
                )
            ],
        },
    ),
    "single_node_multi_container_execution_command_on_interactive_session_success": TestSpec(
        name="single_node_multi_container_execution_command_on_interactive_session_success",
        description=textwrap.dedent("""\
            Test for executing code in an interactive session.
            This test verifies that code can be executed in an interactive session, and that the session transitions through the expected lifecycle events.
            The test will:
            1. Create an interactive session with the specified image and resources.
            2. Execute a command in the session and verify the output.
            3. Assert that the session is running after execution.
            4. Destroy the session after the test is complete.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(InteractiveSessionExecuteCodeSuccess()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
        ),
        parametrizes={
            **CLUSTER_CONFIG_PARAM,
            ContextName.CODE_EXECUTION: [
                CodeExecutionDep(code='print("Hello, world!")', expected_result="Hello, world!\n"),
                CodeExecutionDep(code="1 + 1", expected_result="2"),
            ],
        },
    ),
    "single_node_multi_container_execution_command_on_interactive_session_failure_wrong_command": TestSpec(
        name="single_node_multi_container_execution_command_on_interactive_session_failure_wrong_command",
        description=textwrap.dedent("""\
            Test for executing code in an interactive session.
            This test verifies that code can be executed in an interactive session, and that the session transitions through the expected lifecycle events.
            The test will:
            1. Create an interactive session with the specified image and resources.
            2. Execute a command in the session and verify the output.
            3. Assert that the session is running after execution.
            4. Destroy the session after the test is complete.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(
            InteractiveSessionExecuteCodeFailureWrongCommand()
        ).with_wrappers(KeypairAuthTemplate, InteractiveSessionTemplate),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
    "single_node_multi_container_execution_command_on_interactive_session_failure_with_custom_exitcode": TestSpec(
        name="single_node_multi_container_execution_command_on_interactive_session_failure_with_custom_exitcode",
        description=textwrap.dedent("""\
            Test for executing code in an interactive session.
            This test verifies that code can be executed in an interactive session, and that the session transitions through the expected lifecycle events.
            The test will:
            1. Create an interactive session with the specified image and resources.
            2. Execute a command in the session and verify the output.
            3. Assert that the session is running after execution.
            4. Destroy the session after the test is complete.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(
            InteractiveSessionExecuteCodeFailureWithCustomExitCode()
        ).with_wrappers(KeypairAuthTemplate, InteractiveSessionTemplate),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
    "single_node_multi_container_imagify_interactive_session_success": TestSpec(
        name="single_node_multi_container_imagify_interactive_session_success",
        description=textwrap.dedent("""\
            Test for creating a session with too many containers.
            This test verifies that a session creation fails when the specified container count exceeds the limit.
            The test will:
            1. Create an interactive session with the specified image and resources.
            2. Imagify the session to create a new image.
            3. Assert that the new image is created successfully.
            4. Destroy the session after the test is complete.
            5. Untag the image from the container registry.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.IMAGE,
            TestTag.CONTAINER_REGISTRY,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
            TestTag.REQUIRED_CONTAINER_REGISTRY_CONFIGURATION,
        },
        template=BasicTestTemplate(InteractiveSessionImagifySuccess()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
    "single_node_multi_container_commit_interactive_session_success": TestSpec(
        name="single_node_multi_container_commit_interactive_session_success",
        description=textwrap.dedent("""\
            Test for committing an interactive session.
            This test verifies that an interactive session can be committed successfully, creating a tarfile of the session's state.

            The test will:
            1. Create an interactive session with the specified image and resources.
            2. Commit the session as tarfile.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.IMAGE,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
            TestTag.LONG_RUNNING,
        },
        template=BasicTestTemplate(InteractiveSessionCommitSuccess()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
}

SESSION_TEMPLATE_TEST_SPECS = {
    "single_node_multi_container_creation_interactive_session_success_from_template": TestSpec(
        name="single_node_multi_container_creation_interactive_session_success_from_template",
        description=textwrap.dedent("""\
        Test for creating a session from a template.
        This test verifies that a session can be created from a predefined template, and that it transitions through the expected lifecycle events.
        The test will:
        1. Create a session from the specified template.
        2. Listen for lifecycle events and verify that the session transitions through the expected states.
        3. Assert that the session is running after creation.
        4. Destroy the session after the test is complete.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(NopTestCode()).with_wrappers(
            KeypairAuthTemplate, SessionTemplateTemplate, InteractiveSessionFromTemplateTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
    "single_node_multi_container_creation_batch_session_success_from_template": TestSpec(
        name="single_node_multi_container_creation_batch_session_success_from_template",
        description=textwrap.dedent("""\
        Test for executing a session from a template.
        This test verifies that a session can be executed from a predefined template, and that it transitions through the expected lifecycle events.
        The test will:
        1. Create a session from the specified template.
        2. Listen for lifecycle events and verify that the session transitions through the expected states.
        3. Assert that the session is terminated after completion.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(NopTestCode()).with_wrappers(
            KeypairAuthTemplate, SessionTemplateTemplate, BatchSessionFromTemplateTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
}

SESSION_INFO_RETRIEVER_TEST_SPECS = {
    "single_node_multi_container_session_container_log_retriever": TestSpec(
        name="single_node_multi_container_session_container_log_retriever",
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
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(testcode=TestContainerLogRetriever()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
    "single_node_multi_container_session_dependency_graph_retriever": TestSpec(
        name="single_node_multi_container_session_dependency_graph_retriever",
        description=textwrap.dedent("""
            Retrieve and validate the dependency graph of a compute session,
            ensuring the session name matches and the dependency structure is present.
        """),
        tags={
            TestTag.SESSION,
            TestTag.MANAGER,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(testcode=DependencyGraphRetriever()).with_wrappers(
            KeypairAuthTemplate, BatchSessionTemplate, DependentSessionTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
    "single_node_multi_container_session_status_history": TestSpec(
        name="single_node_multi_container_session_status_history",
        description=textwrap.dedent("""
            Tests retrieval of session status history
            Validate that the status history is not empty and contains valid statuses
        """),
        tags={
            TestTag.SESSION,
            TestTag.MANAGER,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(
            testcode=SessionStatusHistoryRetriever(),
        ).with_wrappers(KeypairAuthTemplate, InteractiveSessionTemplate),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
}

SESSION_RENAME_TEST_SPECS = {
    "single_node_multi_container_session_rename_success": TestSpec(
        name="single_node_multi_container_session_rename_success",
        description=textwrap.dedent("""\
        Test for renaming a session.
        This test verifies that a session can be renamed successfully
        The test will:
        1. Create a session with a specific name.
        2. Rename the session to a new name.
        3. Assert that the session's name has been updated correctly.
        4. Destroy the session after the test is complete.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(testcode=TestSessionRename()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
    "single_node_multi_container_session_rename_fail_duplicated_name": TestSpec(
        name="single_node_multi_container_session_rename_fail_duplicated_name",
        description=textwrap.dedent("""\
        Test for renaming a session to a name that is already taken.
        This test verifies that renaming a session to a duplicate name fails as expected.
        The test will:
        1. Create two sessions with different names.
        2. Attempt to rename the second session to the name of the first session.
        3. Assert that an error is raised due to the name conflict.
        4. Destroy both sessions after the test is complete.
        """),
        tags={
            TestTag.MANAGER,
            TestTag.AGENT,
            TestTag.SESSION,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(testcode=SessionRenameFailureDuplicatedName()).with_wrappers(
            KeypairAuthTemplate, InteractiveSessionTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
}

SESSION_VFOLDER_TEST_SPECS = {
    "single_node_multi_container_session_with_vfolder_mount_works_successfully": TestSpec(
        name="single_node_multi_container_session_with_vfolder_mount_works_successfully",
        description=textwrap.dedent("""
        Test for mounting a virtual folder in a session.
        This test verifies the ability to mount a virtual folder (vfolder) into a session and perform file operations.
        The test will:
        1. Create a session with a vfolder mounted.
        2. Upload a dummy file to the mounted vfolder.
        3. List files in the vfolder and verify the uploaded file exists.
        4. Download the file from the vfolder and verify its content matches the original.
        5. Clean up the session and test files after completion.
        """),
        tags={
            TestTag.SESSION,
            TestTag.VFOLDER,
            TestTag.REQUIRED_SINGLE_NODE_MULTI_CONTAINER_CONFIGURATION,
        },
        template=BasicTestTemplate(testcode=FileHandlingInMountedVFolderSuccess()).with_wrappers(
            KeypairAuthTemplate, ProjectVFolderTemplate, VFolderMountedInteractiveSessionTemplate
        ),
        parametrizes=CLUSTER_CONFIG_PARAM,
    ),
}


SINGLE_NODE_MULTI_CONTAINER_SESSION_TEST_SPECS = {
    **BATCH_SESSION_TEST_SPECS,
    **INTERACTIVE_SESSION_TEST_SPECS,
    **SESSION_TEMPLATE_TEST_SPECS,
    **SESSION_INFO_RETRIEVER_TEST_SPECS,
    **SESSION_RENAME_TEST_SPECS,
    **SESSION_VFOLDER_TEST_SPECS,
}
