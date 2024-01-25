from aiohttp import web

# from ai.backend.manager.api.context import RootContext

# root_context_app_key = web.AppKey("_root.context", RootContext)
api_versions_app_key = web.AppKey("api_versions", tuple[int, ...])
prefix_app_key = web.AppKey("prefix", str)
