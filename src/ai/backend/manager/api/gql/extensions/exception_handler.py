from __future__ import annotations

import asyncio
import logging
<<<<<<< HEAD
from collections.abc import Awaitable, Callable
from typing import Any, Final
=======
from collections.abc import Awaitable, Callable, Iterator
from typing import Any, Final, override
>>>>>>> f09541fb8 (fix(BA-8880): keep SQL and PostgreSQL diagnostics out of GQL error responses (#16463))

from graphql import GraphQLError, GraphQLResolveInfo
from pydantic import ValidationError
from strawberry.exceptions import MissingQueryError
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.schema.exceptions import CannotGetOperationTypeError, InvalidOperationTypeError
from strawberry.types.execution import StreamExecutionResult
from strawberry.utils.await_maybe import AwaitableOrValue

from ai.backend.common.exception import (
    BackendAIError,
    BackendAISchemaValidationFailed,
)
<<<<<<< HEAD
from ai.backend.logging.utils import BraceStyleAdapter
=======
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.errors.common import InternalServerError
from ai.backend.manager.errors.repository import RepositoryIntegrityError
>>>>>>> f09541fb8 (fix(BA-8880): keep SQL and PostgreSQL diagnostics out of GQL error responses (#16463))

log: Final = BraceStyleAdapter(logging.getLogger(__spec__.name))


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
<<<<<<< HEAD
        except BackendAIError as e:
            if e.status_code // 100 == 4:
                log.debug("GraphQL client error: {}", e)
            elif e.status_code // 100 == 5:
                log.exception("GraphQL server error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(e.error_code())},
            ) from e
=======
>>>>>>> f09541fb8 (fix(BA-8880): keep SQL and PostgreSQL diagnostics out of GQL error responses (#16463))
        except ValidationError as e:
            log.debug("GraphQL input validation error: {}", e)
            raise _to_graphql_validation_error(e) from e
        except RepositoryIntegrityError as e:
            # Its message carries the PostgreSQL diagnostic; answer with the title only.
            log.trace("graphql client error", error_code=str(e.error_code()), error_message=str(e))
            raise GraphQLError(
                message=e.error_title, extensions={"code": str(e.error_code())}
            ) from e
        except BackendAIError as e:
            if e.is_client_error():
                log.trace(
                    "graphql client error", error_code=str(e.error_code()), error_message=str(e)
                )
            else:
                log.exception("graphql server error", error_code=str(e.error_code()))
            raise self._wrap_backend_error(e) from e
        except Exception as e:
<<<<<<< HEAD
            log.exception("GraphQL unexpected error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(ErrorCode.default())},
            ) from e
=======
            log.exception("graphql unexpected error")
            raise self._wrap_backend_error(InternalServerError()) from e
>>>>>>> f09541fb8 (fix(BA-8880): keep SQL and PostgreSQL diagnostics out of GQL error responses (#16463))
        if asyncio.iscoroutine(result):
            return self._handle_async(result)
        return result

    async def _handle_async(self, coro: Awaitable[object]) -> object:
        try:
            return await coro
<<<<<<< HEAD
        except BackendAIError as e:
            if e.status_code // 100 == 4:
                log.debug("GraphQL client error: {}", e)
            elif e.status_code // 100 == 5:
                log.exception("GraphQL server error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(e.error_code())},
            ) from e
=======
>>>>>>> f09541fb8 (fix(BA-8880): keep SQL and PostgreSQL diagnostics out of GQL error responses (#16463))
        except ValidationError as e:
            log.debug("GraphQL input validation error: {}", e)
            raise _to_graphql_validation_error(e) from e
        except RepositoryIntegrityError as e:
            # Its message carries the PostgreSQL diagnostic; answer with the title only.
            log.trace("graphql client error", error_code=str(e.error_code()), error_message=str(e))
            raise GraphQLError(
                message=e.error_title, extensions={"code": str(e.error_code())}
            ) from e
        except BackendAIError as e:
            if e.is_client_error():
                log.trace(
                    "graphql client error", error_code=str(e.error_code()), error_message=str(e)
                )
            else:
                log.exception("graphql server error", error_code=str(e.error_code()))
            raise self._wrap_backend_error(e) from e
        except Exception as e:
<<<<<<< HEAD
            log.exception("GraphQL unexpected error: {}", e)
            raise GraphQLError(
                message=str(e),
                extensions={"code": str(ErrorCode.default())},
            ) from e
=======
            log.exception("graphql unexpected error")
            raise self._wrap_backend_error(InternalServerError()) from e

    def _wrap_backend_error(self, e: BackendAIError) -> GraphQLError:
        if e.is_client_error():
            return GraphQLError(message=str(e), extensions={"code": str(e.error_code())})
        return GraphQLError(message=e.error_title, extensions={"code": str(e.error_code())})

    @override
    def on_stream_result(self, result: StreamExecutionResult) -> Iterator[None]:
        # graphql-core does not run resolve() for a subscription's event stream: an error raised
        # while streaming arrives here already caught, so it is matched rather than excepted.
        if result.errors:
            masked: list[GraphQLError] = []
            for error in result.errors:
                converted: GraphQLError
                match error.original_error:
                    case (
                        None
                        | GraphQLError()
                        | MissingQueryError()
                        | CannotGetOperationTypeError()
                        | InvalidOperationTypeError()
                    ):
                        # Messages graphql-core or Strawberry wrote for the client.
                        masked.append(error)
                        continue
                    case ValidationError() as e:
                        log.trace("graphql input validation failed", error_message=str(e))
                        converted = _to_graphql_validation_error(e)
                    case RepositoryIntegrityError() as e:
                        log.trace(
                            "graphql client error",
                            error_code=str(e.error_code()),
                            error_message=str(e),
                        )
                        converted = GraphQLError(
                            e.error_title, extensions={"code": str(e.error_code())}
                        )
                    case BackendAIError() as e if e.is_client_error():
                        log.trace(
                            "graphql client error",
                            error_code=str(e.error_code()),
                            error_message=str(e),
                        )
                        converted = self._wrap_backend_error(e)
                    case BackendAIError() as e:
                        log.error(
                            "graphql server error", exc_info=e, error_code=str(e.error_code())
                        )
                        converted = self._wrap_backend_error(e)
                    case e:
                        log.error("graphql unexpected error", exc_info=e)
                        converted = self._wrap_backend_error(InternalServerError())
                masked.append(
                    GraphQLError(
                        message=converted.message,
                        nodes=error.nodes,
                        path=error.path,
                        extensions=converted.extensions,
                    )
                )
            result.errors = masked
        yield
>>>>>>> f09541fb8 (fix(BA-8880): keep SQL and PostgreSQL diagnostics out of GQL error responses (#16463))
