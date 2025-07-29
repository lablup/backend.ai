import functools


def auth_required(handler):
    from ai.backend.manager.api.auth import AuthorizationFailed

    @functools.wraps(handler)
    async def wrapped(request, *args, **kwargs):
        if request.get("is_authorized", False):
            return await handler(request, *args, **kwargs)
        raise AuthorizationFailed("Unauthorized access")

    from ai.backend.manager.api.utils import set_handler_attr

    set_handler_attr(wrapped, "auth_required", True)
    set_handler_attr(wrapped, "auth_scope", "user")
    return wrapped
