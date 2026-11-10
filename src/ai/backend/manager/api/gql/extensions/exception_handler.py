from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, Final, override

from graphql import GraphQLError, GraphQLResolveInfo
from pydantic import ValidationError
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue

from ai.backend.common.exception import (
    BackendAIError,
    BackendAISchemaValidationFailed,
    ErrorCode,
)
from ai.backend.logging.structured import StructuredLogger

log: Final = StructuredLogger(logging.getLogger(__spec__.name))


def _to_graphql_validation_error(e: ValidationError) -> GraphQLError:
    """Map a raw pydantic ``ValidationError`` to a 400-class GraphQL error."""
    # ``input``/``ctx`` may carry non-JSON-serializable objects.
    errors = e.errors(include_input=False, include_context=False)
    summary = "; ".join(str(err.get("msg", "")) for err in errors)
    converted = BackendAISchemaValidationFailed(extra_msg=summary)
    return GraphQLError(
        message=str(converted),
        extensions={"code": str(converted.error_code()), "errors": errors},
    )


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
        except BackendAIError as e:
            if e.status_code // 100 == 4:
                log.trace(
                    "graphql client error", error_code=str(e.error_code()), error_message=str(e)
                )
            elif e.status_code // 100 == 5:
                log.exception("graphql server error", error_code=str(e.error_code()))
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(e.error_code())},
            ) from e
        except ValidationError as e:
            log.trace("graphql input validation failed", error_message=str(e))
            raise _to_graphql_validation_error(e) from e
        except Exception as e:
            log.exception("graphql unexpected error")
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
                log.trace(
                    "graphql client error", error_code=str(e.error_code()), error_message=str(e)
                )
            elif e.status_code // 100 == 5:
                log.exception("graphql server error", error_code=str(e.error_code()))
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(e.error_code())},
            ) from e
        except ValidationError as e:
            log.trace("graphql input validation failed", error_message=str(e))
            raise _to_graphql_validation_error(e) from e
        except Exception as e:
            log.exception("graphql unexpected error")
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(ErrorCode.default())},
            ) from e
