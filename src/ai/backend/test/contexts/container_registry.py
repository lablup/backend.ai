from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import (
    ContainerRegistryDep,
)


class ContainerRegistriesContext(BaseTestContext[list[ContainerRegistryDep]]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CONTAINER_REGISTRY
