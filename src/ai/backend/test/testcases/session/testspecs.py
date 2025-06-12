from ai.backend.test.templates.auth.keypair import KeypairTemplate
from ai.backend.test.templates.template import BasicTestTemplate
from ai.backend.test.testcases.session.session_creation import TestSessionCreation
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

SESSION_TEST_SPECS = {
    "session_creation": TestSpec(
        name="session_creation",
        description="Test session creation functionality.",
        tags={TestTag.SESSION, TestTag.MANAGER},
        template=BasicTestTemplate(
            testcode=TestSessionCreation(),
            wrapper_templates=[
                KeypairTemplate,
            ],
        ),
    ),
}
