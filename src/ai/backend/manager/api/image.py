from typing import Iterable, Tuple

# import aiohttp_cors
from aiohttp import web

from .types import CORSOptions, WebMiddleware


async def init(app: web.Application) -> None:
    pass


async def shutdown(app: web.Application) -> None:
    pass


def create_app(
    default_cors_options: CORSOptions,
) -> Tuple[web.Application, Iterable[WebMiddleware]]:
    app = web.Application()
    app.on_startup.append(init)
    app.on_shutdown.append(shutdown)
    app["prefix"] = "image"
    app["api_versions"] = (4,)
    # cors = aiohttp_cors.setup(app, defaults=default_cors_options)
    return app, []
