from typing import override

from ai.backend.test.testcases.auth.login import AuthenticationContext
from ai.backend.test.testcases.root import TestRunContext
from ai.backend.test.testcases.template import TestCode, TestTemplate


class TestSessionCreation(TestCode):
    @override
    async def test(self) -> None:
        test_id = TestRunContext.get_test_id()
        session = AuthenticationContext.get_current()

        try:
            await session.ComputeSession.get_or_create(
                image="cr.backend.ai/multiarch/python:3.13-ubuntu24.04",
                name=test_id,
            )
            info = await session.ComputeSession(name=test_id).get_info()

            print(info)
        finally:
            await session.ComputeSession(name=test_id).destroy()


class BasicContainerLogRetrieverTemplate(TestTemplate):
    _test_code: TestSessionCreation

    def __init__(self, testCode: TestSessionCreation) -> None:
        self._test_code = testCode

    @property
    @override
    def name(self) -> str:
        return "session-creation"

    @override
    async def run_test(self, exporter) -> None:
        await self._test_code.test()
