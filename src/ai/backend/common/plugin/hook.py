from __future__ import annotations

import enum
import logging
from abc import ABCMeta, abstractmethod
from typing import Any, Final, List, Optional, Protocol, Sequence, Tuple, Union

import attrs

from ..logging import BraceStyleAdapter
from . import AbstractPlugin, BasePluginContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]

__all__ = (
    "HookHandler",
    "HookPlugin",
    "HookPluginContext",
    "Reject",
    "HookResults",
    "HookResult",
    "HookReturnTiming",
    "PASSED",
    "REJECTED",
    "ERROR",
    "ALL_COMPLETED",
    "FIRST_COMPLETED",
)


class HookHandler(Protocol):
    """
    The handler should accept a single argument containing
    a tuple of parameters passed to the handler.
    If it decides to cancel the ongoing event, it should raise
    :class:`HookDenied` exception.
    """

    async def __call__(self, *args) -> Any:
        # NOTE: Until https://github.com/python/mypy/issues/5876 is resolved,
        #       the get_handlers() in the HookPlugin subclasses should be marked
        #       with "type: ignore" comments.
        ...


class HookPlugin(AbstractPlugin, metaclass=ABCMeta):
    """
    The abstract interface for hook plugins.
    """

    @abstractmethod
    def get_handlers(self) -> Sequence[Tuple[str, HookHandler]]:
        """
        Returns a sequence of pairs of the event name
        and its corresponding handler function.
        """
        pass


class Reject(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class HookResults(enum.Enum):
    PASSED = 0
    REJECTED = 1
    ERROR = 2


class HookReturnTiming(enum.Enum):
    ALL_COMPLETED = 0
    FIRST_COMPLETED = 1


PASSED: Final = HookResults.PASSED
REJECTED: Final = HookResults.REJECTED
ERROR: Final = HookResults.ERROR
ALL_COMPLETED: Final = HookReturnTiming.ALL_COMPLETED
FIRST_COMPLETED: Final = HookReturnTiming.FIRST_COMPLETED


@attrs.define(auto_attribs=True, slots=True)
class HookResult:
    status: HookResults
    src_plugin: Optional[Union[str, Sequence[str]]] = None
    reason: Optional[str] = None
    result: Optional[Any] = None


class HookPluginContext(BasePluginContext[HookPlugin]):
    """
    A manager for hook plugins with convenient handler invocation.
    """

    plugin_group = "backendai_hook_v20"

    def _get_handlers(
        self,
        event_name: str,
        order: Sequence[str] = None,
    ) -> Sequence[Tuple[str, HookHandler]]:
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

    async def dispatch(
        self,
        event_name: str,
        args: Tuple[Any, ...],
        *,
        return_when: HookReturnTiming = ALL_COMPLETED,
        success_if_no_hook: bool = True,
        order: Sequence[str] = None,
    ) -> HookResult:
        """
        Invoke the handlers that matches with the given ``event_name``.
        If any of the handlers raises :class:`HookDenied`,
        the event caller should seize the processing.
        """
        executed_plugin_names = []
        results: List[Any] = []
        for plugin_name, hook_handler in self._get_handlers(event_name, order=order):
            try:
                executed_plugin_names.append(plugin_name)
                result = await hook_handler(*args)
            except Reject as e:
                return HookResult(
                    status=REJECTED,
                    src_plugin=plugin_name,
                    reason=e.reason,
                )
            except Exception as e:
                return HookResult(
                    status=ERROR,
                    src_plugin=plugin_name,
                    reason=repr(e),
                )
            else:
                if return_when == FIRST_COMPLETED:
                    return HookResult(
                        status=PASSED,
                        src_plugin=plugin_name,
                        result=result,
                    )
                else:
                    results.append(result)
        if not success_if_no_hook and not executed_plugin_names:
            return HookResult(
                status=REJECTED,
                src_plugin=executed_plugin_names,  # empty
                result=results,  # empty
            )
        return HookResult(
            status=PASSED,
            src_plugin=executed_plugin_names,
            result=results,
        )

    async def notify(
        self,
        event_name: str,
        args: Tuple[Any, ...],
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
                    "HookPluginContext.notify({}): skipping error in hook handler from {}",
                    event_name,
                    plugin_name,
                )
                continue
