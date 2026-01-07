from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import TypeAlias

import aiohttp_cors
from aiohttp import web
from aiohttp.typedefs import Middleware

from ai.backend.common.data.storage.types import ArtifactStorageImportStep

WebRequestHandler: TypeAlias = Callable[
    [web.Request],
    Awaitable[web.StreamResponse],
]
WebMiddleware: TypeAlias = Middleware

CORSOptions: TypeAlias = Mapping[str, aiohttp_cors.ResourceOptions]


@dataclass
class VFolderStorageSetupResult:
    """Result of VFolderStorage setup for import operations."""

    storage_step_mappings: dict[ArtifactStorageImportStep, str]
    cleanup_callback: Callable[[], None] | None
