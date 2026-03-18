"""
Config DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.config.request import (
    CreateDotfileInput,
    DeleteDotfileInput,
    UpdateBootstrapScriptInput,
    UpdateDotfileInput,
)
from ai.backend.common.dto.manager.v2.config.response import (
    BootstrapScriptNode,
    CreateDotfilePayload,
    DeleteDotfilePayload,
    DotfileListPayload,
    DotfileNode,
    UpdateBootstrapScriptPayload,
    UpdateDotfilePayload,
)
from ai.backend.common.dto.manager.v2.config.types import (
    MAXIMUM_DOTFILE_SIZE,
    DotfileOrderField,
    DotfilePermission,
    DotfileScope,
    OrderDirection,
)

__all__ = (
    # Types
    "MAXIMUM_DOTFILE_SIZE",
    "DotfileOrderField",
    "DotfilePermission",
    "DotfileScope",
    "OrderDirection",
    # Input models (request)
    "CreateDotfileInput",
    "DeleteDotfileInput",
    "UpdateBootstrapScriptInput",
    "UpdateDotfileInput",
    # Node and Payload models (response)
    "BootstrapScriptNode",
    "CreateDotfilePayload",
    "DeleteDotfilePayload",
    "DotfileListPayload",
    "DotfileNode",
    "UpdateBootstrapScriptPayload",
    "UpdateDotfilePayload",
)
