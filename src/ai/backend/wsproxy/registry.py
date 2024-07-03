import datetime
import uuid
from typing import Any

from .defs import RootContext
from .exceptions import ServiceUnavailable
from .types import (
    AppMode,
    Circuit,
    EndpointConfig,
    FrontendMode,
    ProxyProtocol,
    RouteInfo,
    SessionConfig,
)


async def add_circuit(
    root_ctx: RootContext,
    session_info: SessionConfig,
    endpoint_info: EndpointConfig | None,
    app: str,
    protocol: ProxyProtocol,
    mode: AppMode,
    routes: list[RouteInfo],
    *,
    envs: dict[str, Any] = {},
    args: str | None = None,
    open_to_public=False,
    allowed_client_ips: str | None = None,
) -> Circuit:
    port_range_start, port_range_end = root_ctx.local_config.wsproxy.bind_proxy_port_range
    for port in range(port_range_start, port_range_end + 1):
        if port not in root_ctx.proxy_frontend.circuits:
            break
    else:
        raise ServiceUnavailable("Port pool exhausted")

    circuit = Circuit(
        id=uuid.uuid4(),
        app=app,
        protocol=protocol,
        worker=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        app_mode=mode,
        frontend_mode=FrontendMode.PORT,
        envs=envs,
        arguments=args,
        port=port,
        user_id=session_info.user_uuid,
        access_key=session_info.access_key,
        endpoint_id=(endpoint_info.id if endpoint_info else None),
        route_info=routes,
        session_ids=[r.session_id for r in routes],
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        open_to_public=open_to_public,
        allowed_client_ips=allowed_client_ips,
    )
    await root_ctx.proxy_frontend.register_circuit(circuit, routes)
    return circuit
