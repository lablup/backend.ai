import textwrap

from ai.backend.test.templates.auth.keypair import KeypairAuthTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.testcases.session.graph_dependency_retriever import DependencyGraphRetriever
from ai.backend.test.testcases.session.session_creation import TestSessionCreation
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

SESSION_TEST_SPECS = {
    "session_creation": TestSpec(
        name="session_creation",
        description="Test session creation functionality.",
        tags={TestTag.SESSION, TestTag.MANAGER},
        template=BasicTestTemplate(
            testcode=TestSessionCreation(),
        ).with_wrappers(KeypairAuthTemplate),
    ),
    "session_dependency_graph_retriever": TestSpec(
        name="session_dependency_graph_retriever",
        description=textwrap.dedent("""
            Retrieve and validate the dependency graph of a compute session,
            ensuring the session name matches and the dependency structure is present.
        """),
        tags={TestTag.SESSION, TestTag.MANAGER},
        template=BasicTestTemplate(testcode=DependencyGraphRetriever()).with_wrappers(
            KeypairAuthTemplate
        ),
    ),
}
