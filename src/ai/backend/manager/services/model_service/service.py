from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.model_service.actions.clear_error import (
    ClearErrorAction,
    ClearErrorActionResult,
)
from ai.backend.manager.services.model_service.actions.create_service import (
    CreateModelServiceAction,
    CreateModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_route import (
    DeleteRouteAction,
    DeleteRouteActionResult,
)
from ai.backend.manager.services.model_service.actions.delete_service import (
    DeleteModelServiceAction,
    DeleteModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.generate_token import (
    GenerateTokenAction,
    GenerateTokenActionResult,
)
from ai.backend.manager.services.model_service.actions.get_info import (
    GetInfoAction,
    GetInfoActionResult,
)
from ai.backend.manager.services.model_service.actions.list_errors import (
    ListErrorsAction,
    ListErrorsActionResult,
)
from ai.backend.manager.services.model_service.actions.list_service import (
    ListModelServiceAction,
    ListModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.list_supported_runtimes import (
    ListSupportedRuntimesAction,
    ListSupportedRuntimesActionResult,
)
from ai.backend.manager.services.model_service.actions.scale import ScaleAction, ScaleActionResult
from ai.backend.manager.services.model_service.actions.start_service import (
    StartModelServiceAction,
    StartModelServiceActionResult,
)
from ai.backend.manager.services.model_service.actions.sync import SyncAction, SyncActionResult
from ai.backend.manager.services.model_service.actions.update_route import (
    UpdateRouteAction,
    UpdateRouteActionResult,
)


class ModelService:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def list_serve(self, action: ListModelServiceAction) -> ListModelServiceActionResult:
        return ListModelServiceActionResult()

    async def create(self, action: CreateModelServiceAction) -> CreateModelServiceActionResult:
        return CreateModelServiceActionResult()

    async def delete(self, action: DeleteModelServiceAction) -> DeleteModelServiceActionResult:
        return DeleteModelServiceActionResult()

    async def try_start(self, action: StartModelServiceAction) -> StartModelServiceActionResult:
        return StartModelServiceActionResult()

    async def list_supported_runtimes(
        self, action: ListSupportedRuntimesAction
    ) -> ListSupportedRuntimesActionResult:  # noqa: F821
        return ListSupportedRuntimesActionResult()

    async def get_info(self, action: GetInfoAction) -> GetInfoActionResult:
        return GetInfoActionResult()

    async def list_errors(self, action: ListErrorsAction) -> ListErrorsActionResult:
        return ListErrorsActionResult()

    async def clear_error(self, action: ClearErrorAction) -> ClearErrorActionResult:
        return ClearErrorActionResult()

    async def scale(self, action: ScaleAction) -> ScaleActionResult:
        return ScaleActionResult()

    async def sync(self, action: SyncAction) -> SyncActionResult:
        return SyncActionResult()

    async def update_route(self, action: UpdateRouteAction) -> UpdateRouteActionResult:
        return UpdateRouteActionResult()

    async def delete_route(self, action: DeleteRouteAction) -> DeleteRouteActionResult:
        return DeleteRouteActionResult()

    async def generate_token(self, action: GenerateTokenAction) -> GenerateTokenActionResult:
        return GenerateTokenActionResult()
