from ai.backend.common.bgtask.types import BgtaskStatus
from ai.backend.common.json import load_json
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.session import CreatedSessionMetaContext, SessionImagifyContext
from ai.backend.test.templates.template import TestCode


class InteractiveSessionImagifySuccess(TestCode):
    async def test(self) -> None:
        client_session = ClientSessionContext.current()
        session_meta = CreatedSessionMetaContext.current()
        imagify_deps = SessionImagifyContext.current()

        result = await client_session.ComputeSession(str(session_meta.id)).export_to_image(
            imagify_deps.new_image_name,
        )
        bgtask_id = result["task_id"]
        bgtask = client_session.BackgroundTask(bgtask_id)

        new_image_id = None
        async with bgtask.listen_events() as response:
            async for ev in response:
                data = load_json(ev.data)

                match ev.event:
                    case BgtaskStatus.UPDATED:
                        continue
                    case BgtaskStatus.DONE:
                        errors = data.get("errors")
                        if errors:
                            raise RuntimeError(f"Error in bgtask: {errors}")
                        if message := data.get("message"):
                            # Legacy manager will not include an image_id in the message.
                            # In that case, skip the image untagging and consider the test successful.
                            if message != "None":
                                new_image_id = data["message"]
                        break
                    case _:
                        raise RuntimeError(f"Got unexpected event: {ev.event}, data: {data}")
        if new_image_id:
            result = await client_session.Image.untag_image_from_registry(new_image_id)
            assert result["ok"], "Failed to untag image from registry"
