from aiohttp import web


class AuthorizationFailed(web.HTTPUnauthorized):
    pass
