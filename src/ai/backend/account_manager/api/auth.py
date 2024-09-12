from aiohttp import web

from ..types import (
    CORSOptions,
    WebMiddleware,
)


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> tuple[web.Application, list[WebMiddleware]]:
    app = web.Application()
    app["prefix"] = "auth"
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    return app, []
