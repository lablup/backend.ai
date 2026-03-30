from ai.backend.test.templates.auth.login import LoginTemplate
from ai.backend.test.templates.template import BasicTestTemplate, NopTestCode
from ai.backend.test.testcases.spec_manager import TestSpec, TestTag

AUTH_TEST_SPECS = {
    "login": TestSpec(
        name="login",
        description="Test user login functionality.",
        tags={TestTag.WEBSERVER, TestTag.AUTH},
        template=BasicTestTemplate(
            testcode=NopTestCode(),
        ).with_wrappers(
            LoginTemplate,
        ),
    )
}
