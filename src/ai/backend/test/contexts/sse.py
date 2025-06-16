from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import (
    SSEDep,
)


class SSEContext(BaseTestContext[SSEDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SSE
