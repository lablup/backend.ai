from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.model_service import ModelServiceEndpointMeta
from ai.backend.test.tester.dependency import ModelServiceDep


class ModelServiceContext(BaseTestContext[ModelServiceDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.MODEL_SERVICE


class CreatedModelServiceEndpointMetaContext(BaseTestContext[ModelServiceEndpointMeta]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_MODEL_SERVICE_ENDPOINT


class CreatedModelServiceTokenContext(BaseTestContext[str]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_MODEL_SERVICE_TOKEN
