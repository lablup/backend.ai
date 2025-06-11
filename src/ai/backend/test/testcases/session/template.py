import uuid
from contextlib import asynccontextmanager as actxmgr
from typing import AsyncIterator, override

from ai.backend.test.templates.template import SequenceTestTemplate, WrapperTestTemplate
from ai.backend.test.testcases.session.context import ComputeSessionContext


# TODO: How to improve this?
class SessionNameTemplateWrapper(WrapperTestTemplate):
    @property
    @override
    def name(self) -> str:
        return "session_name_setup"

    @override
    @actxmgr
    async def context(self) -> AsyncIterator[None]:
        """
        Context manager to set the compute session for the duration of the context.
        """
        session_name = f"test_session_{uuid.uuid4()}"
        with ComputeSessionContext.with_current(session_name):
            yield


class SessionLifecycleTemplate(SequenceTestTemplate):
    @property
    @override
    def name(self) -> str:
        return "session_lifecycle"
