from __future__ import annotations

from typing import Any


class AgentError(RuntimeError):
    """
    A dummy exception class to distinguish agent-side errors passed via
    aiozmq.rpc calls.

    It carrise two args tuple: the exception type and exception arguments from
    the agent.
    """

    def __init__(self, *args: Any, exc_repr: str | None = None) -> None:
        super().__init__(*args)
        self.exc_repr = exc_repr
