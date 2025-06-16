from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import (
    SSEConfig,
)


class SSEContext(BaseTestContext[SSEConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SSE
