from typing import override

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import ScalingGroupDep


class ScalingGroupContext(BaseTestContext[ScalingGroupDep]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SCALING_GROUP


class ScalingGroupNameContext(BaseTestContext[str]):
    @override
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SCALING_GROUP_NAME
