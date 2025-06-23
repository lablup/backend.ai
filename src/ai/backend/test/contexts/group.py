from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import GroupDep


class GroupContext(BaseTestContext[GroupDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.GROUP
