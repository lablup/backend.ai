from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.group import CreatedGroupMeta
from ai.backend.test.tester.dependency import GroupDep


class GroupContext(BaseTestContext[GroupDep]):
    @classmethod
    @override
    def name(cls) -> ContextName:
        return ContextName.GROUP


class CreatedGroupContext(BaseTestContext[CreatedGroupMeta]):
    @classmethod
    @override
    def name(cls) -> ContextName:
        return ContextName.CREATED_GROUP
