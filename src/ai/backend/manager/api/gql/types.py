# ruff: noqa: E402
from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import attrs

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.manager.api import ManagerStatus
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.idle import IdleCheckerHost
from ai.backend.manager.models.base import DataLoaderManager
from ai.backend.manager.models.storage import StorageSessionManager
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.plugin.network import NetworkPluginContext
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.service.base import ServicesContext
from ai.backend.manager.services.processors import Processors

if TYPE_CHECKING:
    from ai.backend.common.bgtask.bgtask import BackgroundTaskManager
    from ai.backend.common.etcd import AsyncEtcd
    from ai.backend.common.types import (
        SlotName,
        SlotTypes,
    )


@attrs.define(auto_attribs=True, slots=True)
class StrawberryGQLContext:
    dataloader_manager: DataLoaderManager
    config_provider: ManagerConfigProvider
    etcd: AsyncEtcd
    user: Mapping[str, Any]  # TODO: express using typed dict
    access_key: str
    db: ExtendedAsyncSAEngine
    network_plugin_ctx: NetworkPluginContext
    services_ctx: ServicesContext
    valkey_stat: ValkeyStatClient
    valkey_live: ValkeyLiveClient
    valkey_image: ValkeyImageClient
    manager_status: ManagerStatus
    known_slot_types: Mapping[SlotName, SlotTypes]
    background_task_manager: BackgroundTaskManager
    storage_manager: StorageSessionManager
    registry: AgentRegistry
    idle_checker_host: IdleCheckerHost
    metric_observer: GraphQLMetricObserver
    processors: Processors


from enum import StrEnum
from typing import Optional

import orjson
import strawberry


@strawberry.enum
class OrderDirection(StrEnum):
    ASC = "ASC"
    DESC = "DESC"


@strawberry.enum
class Ordering(StrEnum):
    ASC = "ASC"
    ASC_NULLS_FIRST = "ASC_NULLS_FIRST"
    ASC_NULLS_LAST = "ASC_NULLS_LAST"
    DESC = "DESC"
    DESC_NULLS_FIRST = "DESC_NULLS_FIRST"
    DESC_NULLS_LAST = "DESC_NULLS_LAST"


def serialize_json(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return orjson.dumps(value).decode("utf-8")
    elif isinstance(value, str):
        return value
    else:
        return orjson.dumps(value).decode("utf-8")


def parse_json(value: str | bytes) -> Any:
    if isinstance(value, str):
        return orjson.loads(value)
    elif isinstance(value, bytes):
        return orjson.loads(value)
    else:
        return value


@strawberry.scalar(
    name="JSONString",
    description="A custom scalar for JSON strings using orjson",
    serialize=serialize_json,
    parse_value=parse_json,
    parse_literal=lambda v: parse_json(v.value) if hasattr(v, "value") else v,
)
class JSONString:
    pass


@strawberry.input
class StringFilter:
    """String filtering input"""

    contains: Optional[str] = None
    startsWith: Optional[str] = None
    endsWith: Optional[str] = None
    equals: Optional[str] = None
    notEquals: Optional[str] = None
