import logging

import aiohttp
from aiohttp.client_exceptions import ClientConnectorError

from ai.backend.appproxy.common.exceptions import (
    CoordinatorConnectionError,
    InternalServerError,
    ObjectNotFound,
    ServerMisconfiguredError,
    WorkerRegistrationError,
)
from ai.backend.appproxy.common.types import (
    FrontendMode,
    FrontendServerMode,
    SerializableCircuit,
    Slot,
)
from ai.backend.appproxy.common.types import SerializableToken as Token
from ai.backend.common.clients.http_client.client_pool import ClientKey
from ai.backend.logging import BraceStyleAdapter

from .types import (
    LAST_USED_MARKER_SOCKET_NAME,
    Circuit,
    RootContext,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


def _get_coordinator_session(root_ctx: RootContext) -> aiohttp.ClientSession:
    """Get a pooled ClientSession for coordinator requests."""
    coordinator_endpoint = root_ctx.local_config.proxy_worker.coordinator_endpoint
    client_key = ClientKey(
        endpoint=str(coordinator_endpoint),
        domain="coordinator",
    )
    return root_ctx.http_client_pool.load_client_session(client_key)


def _get_request_headers(root_ctx: RootContext, request_id: str) -> dict[str, str]:
    """Get request-specific headers for coordinator API calls."""
    return {
        "X-BackendAI-RequestID": request_id,
        "X-BackendAI-Token": root_ctx.local_config.secrets.api_secret,
    }


async def get_circuit_info(root_ctx: RootContext, request_id: str, circuit_id: str) -> Circuit:
    sess = _get_coordinator_session(root_ctx)
    headers = _get_request_headers(root_ctx, request_id)
    try:
        async with sess.get(f"/api/circuit/{circuit_id}", headers=headers) as resp:
            resp.raise_for_status()
            body = await resp.json()
            return Circuit.from_serialized_circuit(SerializableCircuit(**body))
    except aiohttp.ClientResponseError as e:
        if e.code == 404:
            raise ObjectNotFound(object_name="worker:circuit")
        else:
            log.exception("error while communicating with coordinator:")
            raise InternalServerError from e


async def list_worker_circuits(root_ctx: RootContext, request_id: str) -> list[Circuit]:
    sess = _get_coordinator_session(root_ctx)
    headers = _get_request_headers(root_ctx, request_id)
    try:
        async with sess.get(f"/api/worker/{root_ctx.worker_id}/circuits", headers=headers) as resp:
            resp.raise_for_status()
            body = await resp.json()
            return [
                Circuit.from_serialized_circuit(SerializableCircuit(**c)) for c in body["circuits"]
            ]
    except aiohttp.ClientResponseError as e:
        if e.code == 404:
            raise ObjectNotFound(object_name="worker:worker")
        else:
            log.exception("error while communicating with coordinator:")
            raise InternalServerError from e


async def destroy_circuit(root_ctx: RootContext, request_id: str, circuit_id: str) -> None:
    sess = _get_coordinator_session(root_ctx)
    headers = _get_request_headers(root_ctx, request_id)
    try:
        async with sess.delete(f"/api/circuit/{circuit_id}", headers=headers) as resp:
            resp.raise_for_status()
    except aiohttp.ClientResponseError as e:
        if e.code == 404:
            raise ObjectNotFound(object_name="worker:circuit")
        else:
            log.exception("error while communicating with coordinator:")
            raise InternalServerError from e


async def register_worker(root_ctx: RootContext, request_id: str) -> list[Slot]:
    local_config = root_ctx.local_config
    sess = _get_coordinator_session(root_ctx)
    headers = _get_request_headers(root_ctx, request_id)

    frontend_mode: FrontendServerMode | FrontendMode
    if local_config.proxy_worker.frontend_mode == FrontendServerMode.TRAEFIK:
        if not local_config.proxy_worker.traefik:
            raise ServerMisconfiguredError("worker:proxy-worker.traefik")
        frontend_mode = local_config.proxy_worker.traefik.frontend_mode
    else:
        frontend_mode = local_config.proxy_worker.frontend_mode
    body: dict = {
        "authority": local_config.proxy_worker.authority,
        "frontend_mode": frontend_mode,
        "protocol": local_config.proxy_worker.protocol,
        "hostname": local_config.proxy_worker.api_advertised_addr.host
        if local_config.proxy_worker.api_advertised_addr
        else local_config.proxy_worker.api_bind_addr.host,
        "tls_listen": local_config.proxy_worker.tls_listen,
        "tls_advertised": local_config.proxy_worker.tls_advertised,
        "api_port": local_config.proxy_worker.api_advertised_addr.port
        if local_config.proxy_worker.api_advertised_addr
        else local_config.proxy_worker.api_bind_addr.port,
        "accepted_traffics": local_config.proxy_worker.accepted_traffics,
        "filtered_apps_only": local_config.proxy_worker.filtered_apps_only,
        "app_filters": local_config.proxy_worker.app_filters,
        "traefik_last_used_marker_path": (
            local_config.proxy_worker.traefik.last_used_time_marker_directory
            / LAST_USED_MARKER_SOCKET_NAME
        ).as_posix()
        if local_config.proxy_worker.traefik
        else None,
    }

    match local_config.proxy_worker.frontend_mode:
        case FrontendServerMode.PORT:
            if not local_config.proxy_worker.port_proxy:
                raise ServerMisconfiguredError("worker:proxy-worker.port-proxy")
            body["port_range"] = (
                local_config.proxy_worker.port_proxy.advertised_port_range
                or local_config.proxy_worker.port_proxy.bind_port_range
            )
        case FrontendServerMode.WILDCARD_DOMAIN:
            if not local_config.proxy_worker.wildcard_domain:
                raise ServerMisconfiguredError("worker:proxy-worker.wildcard-domain")
            body["wildcard_domain"] = local_config.proxy_worker.wildcard_domain.domain
            body["wildcard_traffic_port"] = (
                local_config.proxy_worker.wildcard_domain.advertised_port
                or local_config.proxy_worker.wildcard_domain.bind_addr.port
            )
        case FrontendServerMode.TRAEFIK:
            if not local_config.proxy_worker.traefik:
                raise ServerMisconfiguredError("worker:proxy-worker.traefik")
            match local_config.proxy_worker.traefik.frontend_mode:
                case FrontendMode.PORT:
                    if not local_config.proxy_worker.traefik.port_proxy:
                        raise ServerMisconfiguredError("worker:proxy-worker.traefik.port-proxy")
                    body["port_range"] = local_config.proxy_worker.traefik.port_proxy.port_range
                case FrontendMode.WILDCARD_DOMAIN:
                    if not local_config.proxy_worker.traefik.wildcard_domain:
                        raise ServerMisconfiguredError(
                            "worker:proxy-worker.traefik.wildcard-domain"
                        )
                    body["wildcard_domain"] = (
                        local_config.proxy_worker.traefik.wildcard_domain.domain
                    )
                    body["wildcard_traffic_port"] = (
                        local_config.proxy_worker.traefik.wildcard_domain.advertised_port
                    )
    try:
        async with sess.put("/api/worker", json=body, headers=headers) as resp:
            resp.raise_for_status()
            body = await resp.json()
            root_ctx.worker_id = body["id"]
            log.debug(
                "Joined to coordinator {}",
                root_ctx.local_config.proxy_worker.coordinator_endpoint,
            )
            return body["slots"]
    except aiohttp.ClientResponseError as e:
        log.exception("")
        if e.status == 400:
            log.warning("Error from coordinator: {}", e.message)
        raise WorkerRegistrationError(
            extra_data={
                "authority": local_config.proxy_worker.authority,
                "coordinator": str(root_ctx.local_config.proxy_worker.coordinator_endpoint),
            }
        ) from e
    except ClientConnectorError as e:
        raise CoordinatorConnectionError(
            extra_data={
                "authority": local_config.proxy_worker.authority,
                "coordinator": str(root_ctx.local_config.proxy_worker.coordinator_endpoint),
            }
        ) from e


async def deregister_worker(root_ctx: RootContext, request_id: str) -> None:
    sess = _get_coordinator_session(root_ctx)
    headers = _get_request_headers(root_ctx, request_id)
    async with sess.delete(f"/api/worker/{root_ctx.worker_id}", headers=headers) as resp:
        resp.raise_for_status()


async def ping_worker(root_ctx: RootContext, request_id: str) -> None:
    worker_config = root_ctx.local_config.proxy_worker
    sess = _get_coordinator_session(root_ctx)
    headers = _get_request_headers(root_ctx, request_id)
    try:
        async with sess.patch(f"/api/worker/{root_ctx.worker_id}", headers=headers) as resp:
            resp.raise_for_status()
    except ClientConnectorError as e:
        raise CoordinatorConnectionError(
            extra_data={
                "authority": worker_config.authority,
                "coordinator": str(worker_config.coordinator_endpoint),
            }
        ) from e


async def get_token_data(root_ctx: RootContext, request_id: str, token_id: str) -> Token:
    sess = _get_coordinator_session(root_ctx)
    headers = _get_request_headers(root_ctx, request_id)
    async with sess.get(f"/api/worker/token/{token_id}", headers=headers) as resp:
        resp.raise_for_status()
        return Token(**(await resp.json()))
