from typing import override

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.common.types import SessionTypes
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.template import TestCode


class DependencyGraphRetriever(TestCode):
    @override
    async def test(self) -> None:
        test_id = TestIDContext.current()
        session = ClientSessionContext.current()
        image = ImageContext.current()
        first_session_name = f"test-{str(test_id)[:4]}-first"
        second_session_name = f"test-{str(test_id)[:4]}-second"

        try:
            await session.ComputeSession.get_or_create(
                image=image.name,
                name=first_session_name,
                type_=SessionTypes.BATCH,
                startup_command="echo 'Hello, World!'",
            )
            await session.ComputeSession.get_or_create(
                image=image.name,
                name=second_session_name,
                dependencies=[first_session_name],
            )

            result = await session.ComputeSession(name=second_session_name).get_dependency_graph()
            assert result["session_name"] == second_session_name, (
                "Session name in the graph should match the test session name"
            )
            dependencies = result["depends_on"]
            assert dependencies[0]["session_name"] == first_session_name

        finally:
            try:
                # NOTE: Batch sessions should auto-terminate, but we attempt destroy just in case
                await session.ComputeSession(name=first_session_name).destroy()
            except BackendAPIError:
                pass
            await session.ComputeSession(name=second_session_name).destroy()
