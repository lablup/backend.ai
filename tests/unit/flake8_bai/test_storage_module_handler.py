from collections.abc import Callable

type Lint = Callable[[str, str], list[tuple[int, str]]]

STORAGE_API = "src/ai/backend/storage/api/manager.py"


class TestStorageModuleHandlerRule:
    def test_module_handler_fails(self, lint: Lint) -> None:
        source = """
            from aiohttp import web

            async def get_volumes(request: web.Request) -> web.Response:
                return web.json_response({})
        """
        assert lint(STORAGE_API, source) == [(4, "BAI403")]

    def test_module_handler_with_imported_request_fails(self, lint: Lint) -> None:
        source = """
            from aiohttp.web import Request, Response

            @skip_token_auth
            async def check_health(request: Request) -> Response:
                return Response()
        """
        assert lint(STORAGE_API, source) == [(5, "BAI403")]

    def test_handler_class_method_passes(self, lint: Lint) -> None:
        source = """
            from aiohttp import web

            class VolumeHandler:
                @api_handler
                async def get_volumes(self, request: web.Request) -> web.Response:
                    return web.json_response({})
        """
        assert lint(STORAGE_API, source) == []

    def test_module_helper_taking_more_than_request_passes(self, lint: Lint) -> None:
        source = """
            from aiohttp import web

            async def token_auth_middleware(request: web.Request, handler: Handler) -> web.Response:
                return await handler(request)

            async def init_manager_app(ctx: RootContext) -> web.Application:
                return web.Application()
        """
        assert lint(STORAGE_API, source) == []

    def test_module_handler_outside_storage_api_passes(self, lint: Lint) -> None:
        source = """
            from aiohttp import web

            async def get_volumes(request: web.Request) -> web.Response:
                return web.json_response({})
        """
        assert lint("src/ai/backend/storage/server.py", source) == []
