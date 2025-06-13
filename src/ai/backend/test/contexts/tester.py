import uuid

from ai.backend.test.contexts.context import BaseTestContext, ContextName


class TestIDContext(BaseTestContext[uuid.UUID]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.TEST_ID
