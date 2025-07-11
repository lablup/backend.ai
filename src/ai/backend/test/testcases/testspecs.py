from ai.backend.test.testcases.auth.testspecs import AUTH_TEST_SPECS
from ai.backend.test.testcases.group.testspec import GROUP_TEST_SPEC
from ai.backend.test.testcases.model_service.testspecs import MODEL_SERVICE_TEST_SPECS
from ai.backend.test.testcases.session.testspecs import SESSION_TEST_SPECS
from ai.backend.test.testcases.vfolder.testspecs import VFOLDER_TEST_SPECS

ROOT_TEST_SPECS = {
    **AUTH_TEST_SPECS,
    **SESSION_TEST_SPECS,
    **MODEL_SERVICE_TEST_SPECS,
    **VFOLDER_TEST_SPECS,
    **GROUP_TEST_SPEC,
}
