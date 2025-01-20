from typing import AsyncContextManager, Type, TypeVar, cast

import weakref

from aiohttp import web


from ai.backend.storage.api.manager import token_auth_middleware
from ai.backend.storage.api.vfolder.manager_service import VFolderService
from ai.backend.storage.context import RootContext, PrivateContext


T = TypeVar("T")


class VFolderHandler:
    def __init__(self, storage_service: VFolderService) -> None:
        self.storage_service = storage_service

    async def get_volume(self, request: web.Request) -> web.Response:
        return web.Response(text="Volume info")

    async def get_volumes(self, request: web.Request) -> web.Response:
        return web.Response(text="Volumes list")

    async def create_vfolder(self, request: web.Request) -> web.Response:
        return web.Response(text="VFolder created", status=204)

    async def clone_vfolder(self, request: web.Request) -> web.Response:
        return web.Response(text="VFolder cloned", status=204)

    async def get_vfolders(self, request: web.Request) -> web.Response:
        return web.Response(text="VFolders list")

    async def get_vfolder_info(self, request: web.Request) -> web.Response:
        return web.Response(text="VFolder info")

    async def update_vfolder_options(self, request: web.Request) -> web.Response:
        return web.Response(text="VFolder updated")

    async def delete_vfolder(self, request: web.Request) -> web.Response:
        return web.Response(text="VFolder deleted", status=202)

    # async def _extract_params(self, request: web.Request, schema: Type[T]) -> AsyncContextManager[T]:
    #     """
    #     pydantic에서 자주 활용되는 방식 찾아보기
    #     middleware에서 처리하는 방식도 고려해보기"""
    #     data = await request.json()
    #     try:
    #         params = schema(**data)
    #     except TypeError as e:
    #         raise web.HTTPBadRequest(   # Backend.AI의 Exception 패키지 확인하기
    #             reason=f"Invalid request parameters: {str(e)}"
    #         )
    #     # 데이터 검증을 위에서 같이 진행해서 check_params 제외함
    #     return cast(AsyncContextManager[T], params)


async def init_manager_app(ctx: RootContext) -> web.Application:
    storage_service = VFolderService(ctx)
    storage_handler = VFolderHandler(storage_service)

    app = web.Application(
        middlewares=[
            token_auth_middleware,
        ],
    )
    app["ctx"] = ctx
    app["app_ctx"] = PrivateContext(
        deletion_tasks=weakref.WeakValueDictionary())

    # Volume
    app.router.add_route(
        "POST", "/volumes/{volume_id}", storage_handler.get_volume)
    app.router.add_route(
        "GET", "/volumes", storage_handler.get_volumes)
    # VFolder
    app.router.add_route(
        "POST", "/volumes/{volume_id}/vfolders/", storage_handler.create_vfolder
    )
    app.router.add_route(
        "POST", "/volumes/{volume_id}/vfolders/{vfolder_id}/clone", storage_handler.clone_vfolder)
    app.router.add_route(
        "GET", "/volumes/{volume_id}/vfolders", storage_handler.get_vfolders
    )
    app.router.add_route(
        "GET", "/volumes/{volume_id}/vfolders/{vfolder_id}", storage_handler.get_vfolder_info
    )
    app.router.add_route(
        "PUT", "/volumes/{volume_id}/vfolders/{vfolder_id}", storage_handler.update_vfolder_options
    )
    app.router.add_route(
        "DELETE", "/volumes/{volume_id}/vfolders/{vfolder_id}", storage_handler.delete_vfolder
    )

    # evd = ctx.event_dispatcher
    # evd.subscribe(
    #     DoVolumeMountEvent,
    #     storage_service.handle_volume_mount,
    #     name="storage.volume.mount"
    # )
    # evd.subscribe(
    #     DoVolumeUnmountEvent,
    #     storage_service.handle_volume_umount,
    #     name="storage.volume.umount"
    # )

    return app
