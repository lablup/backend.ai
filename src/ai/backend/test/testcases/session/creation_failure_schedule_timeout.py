from ai.backend.client.func.session import ComputeSession
from ai.backend.common.types import ClusterMode
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.image import ImageContext
from ai.backend.test.contexts.tester import TestSpecMetaContext
from ai.backend.test.templates.template import TestCode


class InteractiveSessionCreationFailureScheduleTimeout(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        image_dep = ImageContext.current()
        spec_meta = TestSpecMetaContext.current()
        test_id = spec_meta.test_id
        session_name = f"test_failure_{str(test_id)}"

        resp: ComputeSession = await client_session.ComputeSession.get_or_create(
            image_dep.name,
            architecture=image_dep.architecture,
            name=session_name,
            enqueue_only=False,
            max_wait=5,
            resources={
                "cpu": 9999999999  # Intentionally large value to trigger timeout
            },
            cluster_mode=ClusterMode.SINGLE_NODE,
            cluster_size=1,
        )

        assert resp.status == "TIMEOUT", (
            f"Session should have timed out due to scheduling failure, actual status: {resp.status}"
        )
