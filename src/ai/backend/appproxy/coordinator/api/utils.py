import functools
from typing import Callable, Literal

import jwt
from aiohttp import web
from aiohttp.typedefs import Handler

from ai.backend.appproxy.common.exceptions import AuthorizationFailed
from ai.backend.appproxy.common.utils import set_handler_attr
from ai.backend.appproxy.coordinator.types import RootContext


def auth_required(scope: Literal["manager"] | Literal["worker"]) -> Callable[[Handler], Handler]:
    def wrap(handler: Handler) -> Handler:
        @functools.wraps(handler)
        async def wrapped(request: web.Request, *args, **kwargs):
            root_ctx: RootContext = request.app["_root.context"]
            permitted_token = root_ctx.local_config.secrets.api_secret
            permitted_header_values = (
                permitted_token,
                f"Bearer {permitted_token}",
                f"BackendAI {permitted_token}",
            )
            if _token := request.headers.get("X-BackendAI-Token"):
                if _token not in permitted_header_values:
                    raise AuthorizationFailed("Unauthorized access")
            elif _auth_header := request.headers.get("Authorization"):
                method, _, token = _auth_header.partition(" ")
                match method.lower():
                    case "bearer":
                        try:
                            jwt.decode(
                                token,
                                root_ctx.local_config.secrets.api_secret,
                                algorithms=["HS256"],
                            )
                        except jwt.PyJWTError:
                            raise AuthorizationFailed("Unauthorized access")
                    case _:
                        raise AuthorizationFailed(f"Unsupported authorization method {method}")
            else:
                raise AuthorizationFailed("Unauthorized access")
            return await handler(request, *args, **kwargs)

        original_attrs = getattr(handler, "_backend_attrs", {})
        for k, v in original_attrs.items():
            set_handler_attr(wrapped, k, v)

        set_handler_attr(wrapped, "auth_scope", scope)
        return wrapped

    return wrap
