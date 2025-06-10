import uuid
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.test.testcases.session.context import ComputeSessionContext
from ai.backend.test.testcases.template import WrapperTestTemplate


class SessionTestTemplateWrapper(WrapperTestTemplate):
    @property
    @override
    def name(self) -> str:
        return "session_test"

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        """
        Context manager to set the compute session for the duration of the context.
        """
        session_name = f"test_session_{uuid.uuid4()}"
        async with ComputeSessionContext.with_session(session_name):
            yield
