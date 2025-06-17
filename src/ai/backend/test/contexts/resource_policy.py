from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import (
    KeypairResourcePolicyDep,
)


class KeypairResourcePolicyContext(BaseTestContext[KeypairResourcePolicyDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.KEYPAIR_RESOURCE_POLICY
