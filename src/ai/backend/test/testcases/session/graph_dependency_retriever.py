from typing import override

from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import SessionDependencyContext
from ai.backend.test.templates.template import TestCode


class DependencyGraphRetriever(TestCode):
    @override
    async def test(self) -> None:
        session = ClientSessionContext.current()
        session_dependency = SessionDependencyContext.current()

        for dependent, dependencies in session_dependency.dependencies.items():
            session_name = dependent.name
            result = await session.ComputeSession(name=session_name).get_dependency_graph()

            actual_dependencies = result["depends_on"]
            assert len(actual_dependencies) == len(dependencies), (
                f"Expected {len(dependencies)} dependencies, got {len(actual_dependencies)}"
            )

            actual_dependency_ids = {dep["session_id"] for dep in actual_dependencies}
            expected_dependency_ids = {str(dep.id) for dep in dependencies}

            assert actual_dependency_ids == expected_dependency_ids, (
                f"Expected dependencies {expected_dependency_ids}, "
                f"got {actual_dependency_ids} for session {session_name}"
            )
