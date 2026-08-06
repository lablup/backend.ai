from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Final, override

from graphql import GraphQLError, GraphQLResolveInfo
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.logging.utils import BraceStyleAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


def to_graphql_error(e: Exception) -> GraphQLError:
    """Render an exception as the GraphQL error a client receives."""
    if isinstance(e, BackendAIError):
        if e.status_code // 100 == 4:
            log.debug("GraphQL client error: {}", e)
        elif e.status_code // 100 == 5:
            log.exception("GraphQL server error: {}", e)
        extensions: dict[str, Any] = {"code": str(e.error_code())}
        if e.extra_data is not None:
            extensions["data"] = e.extra_data
        # Not ``str(e)``: it appends a repr of extra_data, which travels in extensions.
        message = f"{e.error_title} ({e.extra_msg})" if e.extra_msg else e.error_title
    else:
        log.exception("GraphQL unexpected error: {}", e)
        extensions = {"code": str(ErrorCode.default())}
        message = str(e)
    return GraphQLError(message=message, extensions=extensions)


async def await_and_convert_errors(coro: Awaitable[object]) -> object:
    """Await an async resolver's result, converting whatever it raises."""
    try:
        result = await coro
    except Exception as e:
        raise to_graphql_error(e) from e
    return result


class GQLExceptionHandlerExtension(SchemaExtension):
    """Transforms internal exceptions into client-safe GraphQL errors with error codes."""

    @override
    def resolve(
        self,
        _next: Callable[..., Any],
        root: Any,
        info: GraphQLResolveInfo,
        *args: Any,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        try:
            result: object = _next(root, info, *args, **kwargs)
        except Exception as e:
            raise to_graphql_error(e) from e
        if asyncio.iscoroutine(result):
            return await_and_convert_errors(result)
        return result
