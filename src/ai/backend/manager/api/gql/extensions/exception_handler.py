from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Final

from graphql import GraphQLError, GraphQLResolveInfo
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue

from ai.backend.common.exception import BackendAIError, ErrorCode
from ai.backend.logging.utils import BraceStyleAdapter

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


class GQLExceptionHandlerExtension(SchemaExtension):
    """Transforms internal exceptions into client-safe GraphQL errors with error codes."""

    def resolve(
        self,
        _next: Callable[..., Any],
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        try:
            result: object = _next(root, info, *args, **kwargs)
        except BackendAIError as e:
            if e.status_code // 100 == 4:
                log.debug("GraphQL client error: {}", e)
            elif e.status_code // 100 == 5:
                log.exception("GraphQL server error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(e.error_code())},
            ) from e
        except Exception as e:
            log.exception("GraphQL unexpected error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(ErrorCode.default())},
            ) from e
        if asyncio.iscoroutine(result):
            return self._handle_async(result)
        return result

    async def _handle_async(self, coro: Awaitable[object]) -> object:
        try:
            return await coro
        except BackendAIError as e:
            if e.status_code // 100 == 4:
                log.debug("GraphQL client error: {}", e)
            elif e.status_code // 100 == 5:
                log.exception("GraphQL server error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(e.error_code())},
            ) from e
        except Exception as e:
            log.exception("GraphQL unexpected error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(ErrorCode.default())},
            ) from e
