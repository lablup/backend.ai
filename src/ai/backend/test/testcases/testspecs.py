from ai.backend.test.templates.auth.keypair import KeypairTemplate
from ai.backend.test.templates.template import BasicTestTemplate, NopTestCode
from ai.backend.test.testcases.auth.testspecs import AUTH_TEST_SPECS
from ai.backend.test.testcases.session.session_creation import TestSessionCreation
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

ROOT_TEST_SPECS = {
    **AUTH_TEST_SPECS,
    "nop": TestSpec(
        name="nop",
        description="No operation test case.",
        tags=set(),
        template=BasicTestTemplate(NopTestCode()),
    ),
    "session": TestSpec(
        name="session",
        description="Test session management.",
        tags={TestTag.SESSION, TestTag.MANAGER},
        template=BasicTestTemplate(
            testcode=TestSessionCreation(),
            wrapper_templates=[
                KeypairTemplate,
            ],
        ),
    ),
}
