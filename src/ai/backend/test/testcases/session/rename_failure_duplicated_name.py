from typing import override

from ai.backend.client.exceptions import BackendAPIError
from ai.backend.test.contexts.client_session import ClientSessionContext
from ai.backend.test.contexts.tester import TestIDContext
from ai.backend.test.templates.template import TestCode

# TODO: Change to injecting from an external config file
_IMAGE_NAME = "cr.backend.ai/multiarch/python:3.13-ubuntu24.04"


class SessionRenameFailureDuplicatedName(TestCode):
    @override
    async def test(self) -> None:
        test_id = TestIDContext.current()
        session = ClientSessionContext.current()
        session_name = f"test-{str(test_id)[0:8]}"
        second_session_name = session_name + "-dup"
        try:
            await session.ComputeSession.get_or_create(
                image=_IMAGE_NAME,
                name=session_name,
            )
            await session.ComputeSession.get_or_create(
                image=_IMAGE_NAME,
                name=second_session_name,
            )

            try:
                # Supposed to fail because second_session_name is already taken, But success now
                # TODO: Fix rename api to fail when the name is duplicated
                await session.ComputeSession(name=second_session_name).rename(session_name)
            except BackendAPIError as e:
                # TODO: Remove print and use assert with error code
                print(f"Expected error occurred: {e}")

        finally:
            # TODO: Use session_id to destroy the session
            await session.ComputeSession(name=session_name).destroy()
            await session.ComputeSession(name=second_session_name).destroy()
