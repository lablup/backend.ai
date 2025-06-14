import textwrap

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.testcases.session.session_creation import TestSessionCreation
from ai.backend.test.testcases.session.status_history_retriever import StatusHistoryRetriever
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

SESSION_TEST_SPECS = {
    "session_creation": TestSpec(
        name="session_creation",
        description="Tests the creation of a session.",
        tags={TestTag.SESSION, TestTag.MANAGER},
        template=BasicTestTemplate(
            testcode=TestSessionCreation(),
        ).with_wrappers(KeypairAuthTemplate),
    ),
    "session_status_history": TestSpec(
        name="session_status_history",
        description=textwrap.dedent("""
            Tests retrieval of session status history
            Validate that the status history is not empty and contains valid statuses
        """),
        tags={TestTag.SESSION, TestTag.MANAGER},
        template=BasicTestTemplate(
            testcode=StatusHistoryRetriever(),
        ).with_wrappers(KeypairAuthTemplate),
    ),
}
