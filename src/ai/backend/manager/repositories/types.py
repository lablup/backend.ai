from dataclasses import dataclass
from typing import Optional

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class RepositoryArgs:
    db: ExtendedAsyncSAEngine
    storage_manager: "StorageSessionManager"
    config_provider: "ManagerConfigProvider"
    valkey_stat_client: "ValkeyStatClient"


@dataclass
class OffsetBasedPaginationOptions:
    """Standard offset/limit pagination options."""

    offset: Optional[int] = None
    limit: Optional[int] = None


@dataclass
class ForwardPaginationOptions:
    """Forward pagination: fetch items after a given cursor."""

    after: Optional[str] = None
    first: Optional[int] = None


@dataclass
class BackwardPaginationOptions:
    """Backward pagination: fetch items before a given cursor."""

    before: Optional[str] = None
    last: Optional[int] = None


@dataclass
class PaginationOptions:
    forward: Optional[ForwardPaginationOptions] = None
    backward: Optional[BackwardPaginationOptions] = None
    offset: Optional[OffsetBasedPaginationOptions] = None
