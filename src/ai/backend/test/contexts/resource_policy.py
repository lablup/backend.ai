from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import UserResourcePolicyDep


class UserResourcePolicyContext(BaseTestContext[UserResourcePolicyDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.USER_RESOURCE_POLICY
