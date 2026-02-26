from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import (
    TYPE_CHECKING,
)

# REST types — canonical location is api.rest.types.
# Re-exported here for backward compatibility during migration.
from .rest.types import (
    AppCreator as AppCreator,
)
from .rest.types import (
    CORSOptions as CORSOptions,
)
from .rest.types import (
    RouteMiddleware as RouteMiddleware,
)
from .rest.types import (
    WebMiddleware as WebMiddleware,
)
from .rest.types import (
    WebRequestHandler as WebRequestHandler,
)

if TYPE_CHECKING:
    from .context import RootContext


type CleanupContext = Callable[["RootContext"], AbstractAsyncContextManager[None]]
