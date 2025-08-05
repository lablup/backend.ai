from dataclasses import dataclass

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
