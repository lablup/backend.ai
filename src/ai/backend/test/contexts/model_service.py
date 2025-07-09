from uuid import UUID

from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.model_service import ModelServiceEndpointMeta
from ai.backend.test.tester.dependency import (
    ModelServiceAutoScalingRuleDep,
    ModelServiceDep,
    ModelServiceScaleReplicasDep,
)


class ModelServiceContext(BaseTestContext[ModelServiceDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.MODEL_SERVICE


class ModelServiceScaleContext(BaseTestContext[ModelServiceScaleReplicasDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.MODEL_SERVICE_SCALE_REPLICAS


class AutoScalingRuleContext(BaseTestContext[ModelServiceAutoScalingRuleDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.MODEL_SERVICE_AUTO_SCALING_RULE


class CreatedModelServiceEndpointMetaContext(BaseTestContext[ModelServiceEndpointMeta]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_MODEL_SERVICE_ENDPOINT


class CreatedModelServiceTokenContext(BaseTestContext[str]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_MODEL_SERVICE_TOKEN


class CreatedAutoScalingRuleIDContext(BaseTestContext[UUID]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_AUTO_SCALING_RULE_ID


class ScaledModelServiceReplicaCountContext(BaseTestContext[int]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.SCALED_MODEL_SERVICE_REPLICA_COUNT
