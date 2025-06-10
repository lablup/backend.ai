from typing import override

from ai.backend.test.testcases.template import TestCode, TestTemplate
from ai.backend.test.testcases.root import test_run_context
from ai.backend.test.testcases.auth.login import authentication_context


class TestContainerLogRetriever(TestCode):
    @override
    async def test(self) -> None:
        test_id = test_run_context.get_test_id()
        session = authentication_context.get_current()

        try:
            compute_session = await session.ComputeSession.get_or_create(
                    image="cr.backend.ai/multiarch/python:3.13-ubuntu24.04",
                    name=test_id,
                )
            if not compute_session:
                raise ValueError("Failed to create compute session")

            info = await session.ComputeSession(name=test_id).get_info()

            print(info)
        finally:
            await session.ComputeSession(name=test_id).destroy()


class BasicContainerLogRetrieverTemplate(TestTemplate):
    _testCode: TestContainerLogRetriever

    def __init__(self, testCode: TestContainerLogRetriever) -> None:
        self._testCode = testCode

    @property
    @override
    def name(self) -> str:
        return "basic-container-log-retriever"

    @override
    async def run_test(self, exporter) -> None:
        await self._testCode.test()
