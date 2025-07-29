import functools

from aiohttp import web


def set_handler_attr(func, key, value):
    attrs = getattr(func, "_backend_attrs", None)
    if attrs is None:
        attrs = {}
    attrs[key] = value
    setattr(func, "_backend_attrs", attrs)


def auth_required_for_method(method):
    @functools.wraps(method)
    async def wrapped(self, request, *args, **kwargs):
        if request.get("is_authorized", False):
            return await method(self, request, *args, **kwargs)
        raise web.HTTPUnauthorized()

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "user")
    return wrapped
