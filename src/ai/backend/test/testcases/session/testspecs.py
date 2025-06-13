import textwrap

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.testcases.session.container_log_retriever import TestContainerLogRetriever
from ai.backend.test.testcases.session.session_creation import TestSessionCreation
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

SESSION_CREATION_TEST_SPECS = {
    "session_creation": TestSpec(
        name="session_creation",
        description="Test session creation functionality.",
        tags={TestTag.SESSION, TestTag.MANAGER},
        template=BasicTestTemplate(
            testcode=TestSessionCreation(),
        ).with_wrappers(KeypairAuthTemplate),
    ),
}

_SESSION_CONTAINER_LOG_RETRIEVER_TEST_SPECS = {
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
            KeypairAuthTemplate
        ),
    ),
}


SESSION_TEST_SPECS = {
    **_SESSION_CONTAINER_LOG_RETRIEVER_TEST_SPECS,
}
