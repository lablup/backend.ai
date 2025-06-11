from typing import override

from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.auth.login import AsyncSessionContext
from ai.backend.test.templates.template import TestCode


class TestSessionCreation(TestCode):
    @override
    async def test(self) -> None:
        test_id = TestIDContext.get_current()
        session = AsyncSessionContext.get_current()
        test_name = f"test-{test_id}"
        try:
            await session.ComputeSession.get_or_create(
                image="cr.backend.ai/multiarch/python:3.13-ubuntu24.04",
                name=test_name,
            )
            info = await session.ComputeSession(name=test_name).get_info()

            print(info)
        finally:
            await session.ComputeSession(name=test_name).destroy()
