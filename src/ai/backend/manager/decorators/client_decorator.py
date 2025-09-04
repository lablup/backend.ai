import asyncio
import logging
import time
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

from ai.backend.common.exception import BackendAIError, UnreachableError
from ai.backend.common.metrics.metric import DomainType, LayerMetricObserver, LayerType
from ai.backend.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


P = ParamSpec("P")
R = TypeVar("R")


def create_layer_aware_client_decorator(
    layer: LayerType,
    default_retry_count: int = 3,
    default_retry_delay: float = 0.1,
):
    """
    Factory function to create layer-aware client decorators.

    Args:
        layer: The layer type for metric observation
        default_retry_count: Default number of retries for client operations
        default_retry_delay: Default delay between retries in seconds

    Returns:
        A client_decorator function configured for the specified layer
    """

    def client_decorator(
        *,
        retry_count: int = default_retry_count,
        retry_delay: float = default_retry_delay,
    ) -> Callable[
        [Callable[P, Coroutine[Any, Any, R]]],
        Callable[P, Coroutine[Any, Any, R]],
    ]:
        """
        Decorator for client operations that adds retry logic and metrics.

        Note: This decorator should only be applied to public methods that are exposed
        to external users. Internal/private methods should not use this decorator.
        """

        def decorator(
            func: Callable[P, Coroutine[Any, Any, R]],
        ) -> Callable[P, Coroutine[Any, Any, R]]:
            observer = LayerMetricObserver.instance()
            operation = func.__name__

            async def wrapper(*args, **kwargs) -> R:
                log.trace("Calling client method {}", operation)
                start = time.perf_counter()
                for attempt in range(retry_count):
                    try:
                        observer.observe_layer_operation_triggered(
                            domain=DomainType.CLIENT,
                            layer=layer,
                            operation=operation,
                        )
                        res = await func(*args, **kwargs)
                        observer.observe_layer_operation(
                            domain=DomainType.CLIENT,
                            layer=layer,
                            operation=operation,
                            success=True,
                            duration=time.perf_counter() - start,
                        )
                        return res
                    except BackendAIError as e:
                        log.exception(
                            "Error in client method {}, args: {}, kwargs: {}, retry_count: {}, error: {}",
                            operation,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.CLIENT,
                            layer=layer,
                            operation=operation,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                        # If it's a BackendAIError, this error is intended to be handled by the caller.
                        raise e
                    except Exception as e:
                        if attempt < retry_count - 1:
                            log.debug(
                                "Error in client method {}, args: {}, kwargs: {}, retry_count: {}, error: {}",
                                operation,
                                args,
                                kwargs,
                                retry_count,
                                e,
                            )
                            observer.observe_layer_retry(
                                domain=DomainType.CLIENT,
                                layer=layer,
                                operation=operation,
                            )
                            await asyncio.sleep(retry_delay)
                            continue
                        log.exception(
                            "Error in client method {}, args: {}, kwargs: {}, retry_count: {}, error: {}",
                            operation,
                            args,
                            kwargs,
                            retry_count,
                            e,
                        )
                        observer.observe_layer_operation(
                            domain=DomainType.CLIENT,
                            layer=layer,
                            operation=operation,
                            success=False,
                            duration=time.perf_counter() - start,
                        )
                        raise e
                raise UnreachableError(
                    f"Reached unreachable code in {operation} after {retry_count} attempts"
                )

            return wrapper

        return decorator

    return client_decorator
