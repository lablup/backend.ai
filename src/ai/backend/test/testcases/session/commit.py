import asyncio

from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import CreatedSessionMetaContext, SessionImagifyContext
from ai.backend.test.contexts.sse import SSEContext
from ai.backend.test.templates.session.utils import verify_bgtask_events
from ai.backend.test.templates.template import TestCode


class InteractiveSessionImagifySuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        session_meta = CreatedSessionMetaContext.current()
        imagify_deps = SessionImagifyContext.current()
        timeout = SSEContext.current().timeout
        result = await client_session.ComputeSession(str(session_meta.id)).export_to_image(
            imagify_deps.new_image_name,
        )

        customized_image_id = await asyncio.wait_for(
            verify_bgtask_events(
                client_session,
                result["task_id"],
                BgtaskStatus.DONE,
                {BgtaskStatus.FAILED, BgtaskStatus.CANCELLED, BgtaskStatus.PARTIAL_SUCCESS},
            ),
            timeout,
        )

        # Legacy manager will not include an `image_id` in message of the response.
        # In that case, just skip the image untagging and consider the test successful.
        if customized_image_id:
            result = await client_session.Image.untag_image_from_registry(customized_image_id)
            assert result["ok"], "Failed to untag image from registry"


class InteractiveSessionCommitSuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        session_meta = CreatedSessionMetaContext.current()

        result = await client_session.ComputeSession(str(session_meta.id)).commit()

        # TODO: This bgtask take a very long time to complete.
        # So, different timeout value should be applied than the SSETimeout.
        await verify_bgtask_events(
            client_session,
            result["bgtask_id"],
            BgtaskStatus.DONE,
            {BgtaskStatus.FAILED, BgtaskStatus.CANCELLED, BgtaskStatus.PARTIAL_SUCCESS},
        )
