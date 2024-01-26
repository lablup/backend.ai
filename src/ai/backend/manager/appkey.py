from aiohttp import web

api_versions_app_key = web.AppKey("api_versions", tuple[int, ...])
prefix_app_key = web.AppKey("prefix", str)
root_app_app_key = web.AppKey("_root_app", web.Application)
