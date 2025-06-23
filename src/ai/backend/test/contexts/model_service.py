from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.tester.dependency import ModelServiceDep


class ModelServiceContext(BaseTestContext[ModelServiceDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.MODEL_SERVICE


class CreatedModelServiceEndpointContext(BaseTestContext[str]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_MODEL_SERVICE_ENDPOINT
