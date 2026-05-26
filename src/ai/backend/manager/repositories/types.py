from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_schedule.client import ValkeyScheduleClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.manager.clients.prometheus.client import PrometheusClient
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops import DBOpsProvider


@dataclass
class RepositoryArgs:
    db: ExtendedAsyncSAEngine
    ops_provider: DBOpsProvider
    storage_manager: StorageSessionManager
    config_provider: ManagerConfigProvider
    valkey_stat_client: ValkeyStatClient
    valkey_schedule_client: ValkeyScheduleClient
    valkey_image_client: ValkeyImageClient
    valkey_live_client: ValkeyLiveClient
    prometheus_client: PrometheusClient
