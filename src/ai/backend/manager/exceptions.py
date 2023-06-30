from __future__ import annotations

import traceback
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    NotRequired,
    Tuple,
    TypedDict,
)

from aiotools import TaskGroupError

if TYPE_CHECKING:
    from ai.backend.common.types import AgentId


class InvalidArgument(Exception):
    """
    An internal exception class to represent invalid arguments in internal APIs.
    This is wrapped as InvalidAPIParameters in web request handlers.
    """

    pass


class AgentError(RuntimeError):
    """
    A dummy exception class to distinguish agent-side errors passed via
    agent rpc calls.

    It carries two args tuple: the exception type and exception arguments from
    the agent.
    """

    __slots__ = (
        "agent_id",
        "exc_name",
        "exc_repr",
        "exc_tb",
    )

    def __init__(
        self,
        agent_id: AgentId,
        exc_name: str,
        exc_repr: str,
        exc_args: Tuple[Any, ...],
        exc_tb: str = None,
    ) -> None:
        super().__init__(agent_id, exc_name, exc_repr, exc_args, exc_tb)
        self.agent_id = agent_id
        self.exc_name = exc_name
        self.exc_repr = exc_repr
        self.exc_args = exc_args
        self.exc_tb = exc_tb


class MultiAgentError(TaskGroupError):
    """
    An exception that is a collection of multiple errors from multiple agents.
    """


class ErrorDetail(TypedDict):
    src: str
    name: str
    repr: str
    agent_id: NotRequired[str]
    collection: NotRequired[List[ErrorDetail]]
    traceback: NotRequired[str]


class ErrorStatusInfo(TypedDict):
    error: ErrorDetail


def convert_to_status_data(
    e: Exception,
    is_debug: bool = False,
    *,
    src: str | None = None,
) -> ErrorStatusInfo:
    data: ErrorStatusInfo
    match e:
        case MultiAgentError():
            return {
                "error": {
                    "src": "agent",
                    "name": "MultiAgentError",
                    "repr": f"MultiAgentError({len(e.__errors__)})",
                    "collection": [
                        convert_to_status_data(sub_error, is_debug, src="agent")["error"]
                        for sub_error in e.__errors__
                    ],
                },
            }
        case AgentError():
            data = {
                "error": {
                    "src": "agent",
                    "name": e.exc_name,
                    "repr": e.exc_repr,
                },
            }
            if is_debug:
                data["error"]["agent_id"] = e.agent_id
                data["error"]["traceback"] = e.exc_tb or ""
            return data
        case _:
            data = {
                "error": {
                    "src": "other" if src is None else src,
                    "name": e.__class__.__name__,
                    "repr": repr(e),
                },
            }
            if is_debug:
                data["error"]["traceback"] = "\n".join(traceback.format_tb(e.__traceback__))
            return data
