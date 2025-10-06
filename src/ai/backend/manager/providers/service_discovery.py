from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager as actxmgr
from typing import TYPE_CHECKING

from ai.backend.common.defs import RedisRole
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.service_discovery.etcd_discovery.service_discovery import (
    ETCDServiceDiscovery,
    ETCDServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.redis_discovery.service_discovery import (
    RedisServiceDiscovery,
    RedisServiceDiscoveryArgs,
)
from ai.backend.common.service_discovery.service_discovery import (
    ServiceDiscoveryLoop,
    ServiceEndpoint,
    ServiceMetadata,
)
from ai.backend.common.types import ServiceDiscoveryType
from ai.backend.logging.otel import OpenTelemetrySpec

if TYPE_CHECKING:
    from ..api.context import RootContext


@actxmgr
async def service_discovery_ctx(root_ctx: RootContext) -> AsyncIterator[None]:
    from .. import __version__

    sd_type = root_ctx.config_provider.config.service_discovery.type
    match sd_type:
        case ServiceDiscoveryType.ETCD:
            root_ctx.service_discovery = ETCDServiceDiscovery(
                ETCDServiceDiscoveryArgs(root_ctx.etcd)
            )
        case ServiceDiscoveryType.REDIS:
            live_valkey_target = root_ctx.valkey_profile_target.profile_target(RedisRole.LIVE)
            root_ctx.service_discovery = await RedisServiceDiscovery.create(
                RedisServiceDiscoveryArgs(valkey_target=live_valkey_target)
            )

    root_ctx.sd_loop = ServiceDiscoveryLoop(
        sd_type,
        root_ctx.service_discovery,
        ServiceMetadata(
            display_name=f"manager-{root_ctx.config_provider.config.manager.id}",
            service_group="manager",
            version=__version__,
            endpoint=ServiceEndpoint(
                address=root_ctx.config_provider.config.manager.announce_addr.address,
                port=root_ctx.config_provider.config.manager.announce_addr.port,
                protocol="http",
                prometheus_address=root_ctx.config_provider.config.manager.announce_internal_addr.address,
            ),
        ),
    )

    if root_ctx.config_provider.config.otel.enabled:
        meta = root_ctx.sd_loop.metadata
        otel_spec = OpenTelemetrySpec(
            service_id=meta.id,
            service_name=meta.service_group,
            service_version=meta.version,
            log_level=root_ctx.config_provider.config.otel.log_level,
            endpoint=root_ctx.config_provider.config.otel.endpoint,
        )
        BraceStyleAdapter.apply_otel(otel_spec)
    yield
    root_ctx.sd_loop.close()
