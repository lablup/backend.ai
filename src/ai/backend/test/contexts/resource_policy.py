from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import UserResourcePolicyDep


class UserResourcePolicyContext(BaseTestContext[UserResourcePolicyDep]):
    @classmethod
    @override
    def name(cls) -> ContextName:
        return ContextName.USER_RESOURCE_POLICY
