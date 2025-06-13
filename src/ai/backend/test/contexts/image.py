from ai.backend.test.testcases.context import BaseTestContext
from ai.backend.test.tester.config import Image


class ImageContext(BaseTestContext[Image]):
    @classmethod
    def name(cls) -> str:
        return "image"
