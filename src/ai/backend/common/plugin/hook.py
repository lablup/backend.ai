from __future__ import annotations

import enum
import logging
from abc import ABCMeta, abstractmethod
from collections.abc import Sequence
from typing import Any, Final, Protocol, cast, override

import attrs

from ai.backend.common.exception import UnreachableError
from ai.backend.logging.structured import StructuredLogger

from . import AbstractPlugin, BasePluginContext

log = StructuredLogger(logging.getLogger(__spec__.name))

__all__ = (
    "ALL_HANDLERS_RUNNER",
    "ERROR",
    "FIRST_HANDLED_RUNNER",
    "PASSED",
    "REJECTED",
    "HookHandler",
    "HookHandlerRunner",
    "HookPlugin",
    "HookPluginContext",
    "HookResult",
    "HookResults",
    "Reject",
)


class HookHandler(Protocol):
    """
    Returns None when the handler does not handle the event, and a non-None result when it does.
    Raises :class:`Reject` to reject the event.
    """

    async def __call__(self, *args: Any) -> Any:
        # NOTE: Until https://github.com/python/mypy/issues/5876 is resolved,
        #       the get_handlers() in the HookPlugin subclasses should be marked
        #       with "type: ignore" comments.
        ...


class HookPlugin(AbstractPlugin, metaclass=ABCMeta):
    """
    The abstract interface for hook plugins.
    """

    @abstractmethod
    def get_handlers(self) -> Sequence[tuple[str, HookHandler]]:
        """
        Returns a sequence of pairs of the event name
        and its corresponding handler function.
        """
        pass


class Reject(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class HookResults(enum.Enum):
    PASSED = 0
    REJECTED = 1
    ERROR = 2


PASSED: Final = HookResults.PASSED
REJECTED: Final = HookResults.REJECTED
ERROR: Final = HookResults.ERROR


@attrs.define(auto_attribs=True, slots=True)
class HookResult[TResult = Any]:
    status: HookResults
    src_plugin: str | Sequence[str] | None = None
    reason: str | None = None
    result: TResult | None = None

    def passed_result(self) -> TResult:
        """
        Returns ``result`` of a PASSED dispatch, which is what the ``HookHandlerRunner[TResult]`` made.
        Only a failed dispatch leaves ``result`` unset, so this raises on one.
        """
        if self.status != PASSED:
            raise UnreachableError(f"A {self.status.name} hook result has no result")
        return cast(TResult, self.result)


class HookHandlerRunner[TResult](metaclass=ABCMeta):
    """
    Decides how many handlers of an event run and what :class:`HookResult` they make.
    """

    @abstractmethod
    async def run_handlers(
        self,
        handlers: Sequence[tuple[str, HookHandler]],
        args: tuple[Any, ...],
    ) -> HookResult[TResult]:
        raise NotImplementedError

    def _build_failed_hook_result(self, plugin_name: str, error: Exception) -> HookResult[TResult]:
        match error:
            case Reject():
                return HookResult(status=REJECTED, src_plugin=plugin_name, reason=error.reason)
            case _:
                return HookResult(status=ERROR, src_plugin=plugin_name, reason=repr(error))


class FirstHandledRunner(HookHandlerRunner[Any]):
    """
    Returns the result of the first handler that handles the event, or None when none does.
    """

    @override
    async def run_handlers(
        self,
        handlers: Sequence[tuple[str, HookHandler]],
        args: tuple[Any, ...],
    ) -> HookResult[Any]:
        executed_plugin_names: list[str] = []
        for plugin_name, hook_handler in handlers:
            executed_plugin_names.append(plugin_name)
            try:
                handler_result = await hook_handler(*args)
            except Exception as e:
                return self._build_failed_hook_result(plugin_name, e)
            if handler_result is not None:
                return HookResult(status=PASSED, src_plugin=plugin_name, result=handler_result)
        return HookResult(status=PASSED, src_plugin=executed_plugin_names, result=None)


class AllHandlersRunner(HookHandlerRunner[list[Any]]):
    """
    Runs every handler and returns the list of their results.
    """

    @override
    async def run_handlers(
        self,
        handlers: Sequence[tuple[str, HookHandler]],
        args: tuple[Any, ...],
    ) -> HookResult[list[Any]]:
        executed_plugin_names: list[str] = []
        handler_results: list[Any] = []
        for plugin_name, hook_handler in handlers:
            executed_plugin_names.append(plugin_name)
            try:
                handler_results.append(await hook_handler(*args))
            except Exception as e:
                return self._build_failed_hook_result(plugin_name, e)
        return HookResult(status=PASSED, src_plugin=executed_plugin_names, result=handler_results)


ALL_HANDLERS_RUNNER: Final = AllHandlersRunner()
FIRST_HANDLED_RUNNER: Final = FirstHandledRunner()


class HookPluginContext(BasePluginContext[HookPlugin]):
    """
    A manager for hook plugins with convenient handler invocation.
    """

    plugin_group = "backendai_hook_v20"

    def _get_handlers(
        self,
        event_name: str,
        order: Sequence[str] | None = None,
    ) -> Sequence[tuple[str, HookHandler]]:
        handlers = []
        for plugin_name, plugin_instance in self.plugins.items():
            for hooked_event_name, hook_handler in plugin_instance.get_handlers():
                if event_name != hooked_event_name:
                    continue
                handlers.append((plugin_name, hook_handler))
        if order is not None:
            non_empty_order = order
            handlers.sort(key=lambda item: non_empty_order.index(item))
        else:
            # the default is alphabetical order with plugin names
            handlers.sort(key=lambda item: item[0])
        return handlers

    async def dispatch[TResult](
        self,
        event_name: str,
        args: tuple[Any, ...],
        *,
        handler_runner: HookHandlerRunner[TResult],
        success_if_no_hook: bool = True,
        order: Sequence[str] | None = None,
    ) -> HookResult[TResult]:
        """
        Invokes the handlers of ``event_name`` in order with ``handler_runner``.
        A handler raising :class:`Reject` or any other exception ends the dispatch.
        """
        handlers = self._get_handlers(event_name, order=order)
        if not handlers and not success_if_no_hook:
            return HookResult(status=REJECTED, src_plugin=[])
        return await handler_runner.run_handlers(handlers, args)

    async def notify(
        self,
        event_name: str,
        args: tuple[Any, ...],
    ) -> None:
        """
        Invoke the handlers that matches with the given ``event_name``.
        Regardless of the handler results, the processing continues.
        """
        for plugin_name, hook_handler in self._get_handlers(event_name):
            try:
                await hook_handler(*args)
            except Exception:
                log.exception(
                    "hook handler failed, skipped",
                    event_name=event_name,
                    plugin_name=plugin_name,
                )
                continue
