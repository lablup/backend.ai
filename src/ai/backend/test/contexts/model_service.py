from ai.backend.test.contexts.context import BaseTestContext, ContextName
from ai.backend.test.data.model_service import CreatedModelServiceMeta
from ai.backend.test.tester.dependency import ModelServiceDep


class ModelServiceContext(BaseTestContext[ModelServiceDep]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.MODEL_SERVICE


class CreatedModelServiceMetaContext(BaseTestContext[CreatedModelServiceMeta]):
    @classmethod
    def name(cls) -> ContextName:
        return ContextName.CREATED_MODEL_SERVICE_META
