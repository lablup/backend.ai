from typing import override

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
        test_name = f"test-{test_id}"
        await session.ComputeSession.get_or_create(
            image=image.name,
            name=test_name,
        )

        result = await session.ComputeSession(name=test_name).get_dependency_graph()
        print(f"Dependency graph for session {test_name}: {result}")
        assert result["session_name"] == test_name, (
            "Session name in the graph should match the test session name"
        )
        assert "depends_on" in result, "Dependency graph should contain 'depends_on' field"

        await session.ComputeSession(name=test_name).destroy()
