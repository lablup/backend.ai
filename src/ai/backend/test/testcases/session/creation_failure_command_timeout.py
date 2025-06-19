import asyncio

from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.session import SessionContext
from ai.backend.test.templates.session.utils import verify_session_events
from ai.backend.test.templates.template import TestCode

_TASK_TIMEOUT = 15


class BatchSessionCreationFailureTimeout(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        image_dep = ImageContext.current()
        session_dep = SessionContext.current()

        session_name = "test-batch-session-execution-failure"
        listener = asyncio.create_task(
            asyncio.wait_for(
                verify_session_events(
                    client_session,
                    session_name,
                    "session_failure",
                    {"session_success", "session_cancelled"},
                    expected_failure_reason="task-timeout",
                ),
                _TASK_TIMEOUT,
            )
        )

        await client_session.ComputeSession.get_or_create(
            image_dep.name,
            architecture=image_dep.architecture,
            name=session_name,
            type_="batch",
            startup_command="sleep 10",
            batch_timeout=3,
            resources=session_dep.resources,
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
        )

        await listener
