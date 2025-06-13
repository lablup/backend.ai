from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import Image


class ImageContext(BaseTestContext[Image]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.IMAGE
