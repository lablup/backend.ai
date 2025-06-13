import textwrap

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.testcases.session.rename_failure_duplicated_name import (
    SessionRenameFailureDuplicatedName,
)
from ai.backend.test.testcases.session.session_creation import TestSessionCreation
from ai.backend.test.testcases.session.session_rename import TestSessionRename
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

_SESSION_CREATION_TEST_SPECS = {
    "session_creation": TestSpec(
        name="session_creation",
        description="Test session creation functionality.",
        tags={TestTag.SESSION, TestTag.MANAGER},
        template=BasicTestTemplate(
            testcode=TestSessionCreation(),
        ).with_wrappers(KeypairAuthTemplate),
    ),
}

_SESSION_RENAME_TEST_SPECS = {
    "session_rename_success": TestSpec(
        name="session_rename_success",
        description=textwrap.dedent("""\
        Test for renaming a session.
        This test verifies that a session can be renamed successfully
        The test will:
        1. Create a session with a specific name.
        2. Rename the session to a new name.
        3. Assert that the session's name has been updated correctly.
        4. Destroy the session after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(testcode=TestSessionRename()).with_wrappers(KeypairAuthTemplate),
    ),
    "session_rename_fail_duplicated_name": TestSpec(
        name="session_rename_fail_duplicated_name",
        description=textwrap.dedent("""\
        Test for renaming a session to a name that is already taken.
        This test verifies that renaming a session to a duplicate name fails as expected.
        The test will:
        1. Create two sessions with different names.
        2. Attempt to rename the second session to the name of the first session.
        3. Assert that an error is raised due to the name conflict.
        4. Destroy both sessions after the test is complete.
        """),
        tags={TestTag.MANAGER, TestTag.AGENT, TestTag.SESSION},
        template=BasicTestTemplate(testcode=SessionRenameFailureDuplicatedName()).with_wrappers(
            KeypairAuthTemplate
        ),
    ),
}

SESSION_TEST_SPECS = {
    **_SESSION_CREATION_TEST_SPECS,
    **_SESSION_RENAME_TEST_SPECS,
}
