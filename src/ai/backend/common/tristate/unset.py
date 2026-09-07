"""The sentinel marking a request field the client did not send.

``Unset`` is a plain alias so that ``isinstance`` accepts it; a PEP 695 ``type`` alias
would not. Background: `common/tristate/KNOWLEDGE.md`.
"""

from pydantic_core import MISSING
from typing_extensions import Sentinel

__all__ = (
    "UNSET",
    "Unset",
)

Unset = Sentinel
UNSET = MISSING
