from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.template import TestCode


class StatusHistoryRetriever(TestCode):
    @override
    async def test(self) -> None:
        test_id = TestIDContext.current()
        session = ClientSessionContext.current()
        image = ImageContext.current()
        test_name = f"test-{test_id}"
        await session.ComputeSession.get_or_create(
            image=image.name,
            name=test_name,
        )

        try:
            result = await session.ComputeSession(name=test_name).get_status_history()
            assert result["result"] != "", "Status history should not be empty"
            # NOTE: SessionStatus enum is not available due to BUILD rules
            # NOTE: src/ai/backend/test/BUILD[//src/ai/backend/**] -> src/ai/backend/manager/BUILD[!*] : DENY
            # expected_status = [status.value for status in SessionStatus]
            # for status_key, status_value in result["result"].items():
            #     assert status_key in expected_status, f"Status {status_key} not in SessionStatus enum"
        finally:
            await session.ComputeSession(name=test_name).destroy()
