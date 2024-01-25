from aiohttp import web

from ai.backend.storage.context import RootContext

ctx_app_key = web.AppKey("ctx", RootContext)
prefix_app_key = web.AppKey("prefix", str)
