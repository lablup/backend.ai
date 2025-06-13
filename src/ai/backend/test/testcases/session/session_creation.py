from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.template import TestCode


class TestSessionCreation(TestCode):
    @override
    async def test(self) -> None:
        test_id = TestIDContext.current()
        session = ClientSessionContext.current()
        image = ImageContext.current()
        test_name = f"test-{test_id}"
        try:
            await session.ComputeSession.get_or_create(
                image=image.name,
                name=test_name,
            )
            info = await session.ComputeSession(name=test_name).get_info()
            if info["image"] != image.name:
                raise ValueError(f"Image mismatch: expected {image.name}, got {info['image']}")
        finally:
            await session.ComputeSession(name=test_name).destroy()
