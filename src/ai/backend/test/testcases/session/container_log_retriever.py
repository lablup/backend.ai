from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.template import TestCode

# TODO: Change to injecting from an external config file
_IMAGE_NAME = "cr.backend.ai/multiarch/python:3.13-ubuntu24.04"


class TestContainerLogRetriever(TestCode):
    @override
    async def test(self) -> None:
        test_id = TestIDContext.current()
        session = ClientSessionContext.current()
        test_name = f"test-{test_id}"
        try:
            result = await session.ComputeSession.get_or_create(
                image=_IMAGE_NAME,
                name=test_name,
            )
            session_id = result.id
            if not session_id:
                raise ValueError("Failed to create or retrieve session ID.")
            # session_info = await session.ComputeSession.from_session_id(
            #     session_id=session_id
            # ).detail()
            # main_kernel_id = session_info["kernels"][0]["id"]
            # result = await session.ComputeSession(name=test_name).get_logs(kernel_id=main_kernel_id)
            # assert result["result"]["logs"] is not None
            # assert result["result"]["logs"] != ""

        finally:
            await session.ComputeSession(name=test_name).destroy()
