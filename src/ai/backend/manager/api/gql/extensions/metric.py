from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from graphql import get_named_type, is_leaf_type
from opentelemetry import trace
from opentelemetry.trace import StatusCode
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.utils.await_maybe import AwaitableOrValue

from ai.backend.common.exception import BackendAIError, ErrorCode

if TYPE_CHECKING:
    from graphql import GraphQLResolveInfo


class GQLMetricExtension(SchemaExtension):
    """Records per-field GraphQL metrics with OpenTelemetry tracing."""

    def resolve(
        self,
        _next: Callable[..., AwaitableOrValue[object]],
        root: Any,
        info: GraphQLResolveInfo,
        *args: str,
        **kwargs: Any,
    ) -> AwaitableOrValue[object]:
        if is_leaf_type(get_named_type(info.return_type)):
            return _next(root, info, *args, **kwargs)

        ctx = info.context
        metric_observer = ctx.metric_observer

        operation_type = info.operation.operation.value
        field_name = info.field_name
        parent_type = info.parent_type.name
        operation_name = (
            info.operation.name.value if info.operation.name is not None else "anonymous"
        )

        tracer = trace.get_tracer(__name__)
        span = tracer.start_span(
            f"gql.{operation_name}.{field_name}",
            attributes={
                "graphql.operation_name": operation_name,
                "graphql.field_name": field_name,
                "graphql.parent_type": parent_type,
            },
        )

        def _set_span(*, error: BaseException | None = None, end_span: bool = False) -> None:
            if error is not None:
                span.record_exception(error)
                span.set_status(StatusCode.ERROR, str(error))
            else:
                span.set_status(StatusCode.OK)
            if end_span:
                span.end()

        def _observe(*, duration: float, error: BaseException | None = None) -> None:
            match error:
                case None:
                    error_code = None
                case BackendAIError():
                    error_code = error.error_code()
                case _:
                    error_code = ErrorCode.default()
            metric_observer.observe_request(
                operation_type=operation_type,
                field_name=field_name,
                parent_type=parent_type,
                operation_name=operation_name,
                error_code=error_code,
                success=error is None,
                duration=duration,
            )

        async def _observe_coroutine(coro: Awaitable[Any]) -> Any:
            with trace.use_span(
                span,
                end_on_exit=True,
                record_exception=False,
                set_status_on_exception=False,
            ):
                start = time.perf_counter()
                try:
                    result = await coro
                    _set_span()
                    _observe(duration=time.perf_counter() - start)
                except BaseException as e:
                    _set_span(error=e)
                    _observe(duration=time.perf_counter() - start, error=e)
                    raise
                return result

        with trace.use_span(
            span,
            end_on_exit=False,
            record_exception=False,
            set_status_on_exception=False,
        ):
            start = time.perf_counter()
            try:
                res = _next(root, info, *args, **kwargs)
                if asyncio.iscoroutine(res):
                    return _observe_coroutine(res)
                _set_span(end_span=True)
                _observe(duration=time.perf_counter() - start)
            except BaseException as e:
                _set_span(error=e, end_span=True)
                _observe(duration=time.perf_counter() - start, error=e)
                raise
            return res
