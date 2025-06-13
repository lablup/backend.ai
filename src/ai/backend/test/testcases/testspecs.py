from ai.backend.test.testcases.auth.testspecs import AUTH_TEST_SPECS
from ai.backend.test.testcases.session.testspecs import SESSION_TEST_SPECS

ROOT_TEST_SPECS = {
    **AUTH_TEST_SPECS,
    **SESSION_TEST_SPECS,
}
