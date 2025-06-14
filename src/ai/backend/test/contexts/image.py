from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.config import (
    ImageConfig,
)


class ImageConfigContext(BaseTestContext[ImageConfig]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.IMAGE
