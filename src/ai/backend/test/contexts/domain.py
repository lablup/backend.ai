from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import DomainDep


class DomainContext(BaseTestContext[DomainDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.DOMAIN
