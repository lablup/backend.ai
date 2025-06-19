from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import ScalingGroupDep


class ScalingGroupContext(BaseTestContext[ScalingGroupDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SCALING_GROUP
