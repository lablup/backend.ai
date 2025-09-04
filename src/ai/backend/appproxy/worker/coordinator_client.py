import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

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
from ai.backend.logging import BraceStyleAdapter

from .types import (
    LAST_USED_MARKER_SOCKET_NAME,
    Circuit,
    RootContext,
)

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@asynccontextmanager
async def coordinator_request_context(
    request_id: str, root_context: RootContext
) -> AsyncIterator[aiohttp.ClientSession]:
    coordinator_endpoint = root_context.local_config.proxy_worker.coordinator_endpoint
    verify_coordinator_ssl_certificate = (
        root_context.local_config.proxy_worker.verify_coordinator_ssl_certificate
    )
    async with aiohttp.ClientSession(
        base_url=str(coordinator_endpoint),
        headers={
            "X-BackendAI-RequestID": request_id,
            "X-BackendAI-Token": root_context.local_config.secrets.api_secret,
        },
        connector=aiohttp.TCPConnector(verify_ssl=verify_coordinator_ssl_certificate),
    ) as sess:
        yield sess


async def get_circuit_info(root_ctx: RootContext, request_id: str, circuit_id: str) -> Circuit:
    async with coordinator_request_context(request_id, root_ctx) as sess:
        try:
            async with sess.get(f"/api/circuit/{circuit_id}") as resp:
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
    async with coordinator_request_context(request_id, root_ctx) as sess:
        try:
            async with sess.get(f"/api/worker/{root_ctx.worker_id}/circuits") as resp:
                resp.raise_for_status()
                body = await resp.json()
                return [
                    Circuit.from_serialized_circuit(SerializableCircuit(**c))
                    for c in body["circuits"]
                ]
        except aiohttp.ClientResponseError as e:
            if e.code == 404:
                raise ObjectNotFound(object_name="worker:worker")
            else:
                log.exception("error while communicating with coordinator:")
                raise InternalServerError from e


async def destroy_circuit(root_ctx: RootContext, request_id: str, circuit_id: str) -> None:
    async with coordinator_request_context(request_id, root_ctx) as sess:
        try:
            async with sess.delete(f"/api/circuit/{circuit_id}") as resp:
                resp.raise_for_status()
        except aiohttp.ClientResponseError as e:
            if e.code == 404:
                raise ObjectNotFound(object_name="worker:circuit")
            else:
                log.exception("error while communicating with coordinator:")
                raise InternalServerError from e


async def register_worker(root_ctx: RootContext, request_id: str) -> list[Slot]:
    local_config = root_ctx.local_config
    async with coordinator_request_context(request_id, root_ctx) as sess:
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
            async with sess.put("/api/worker", json=body) as resp:
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
    async with coordinator_request_context(request_id, root_ctx) as sess:
        async with sess.delete(f"/api/worker/{root_ctx.worker_id}") as resp:
            resp.raise_for_status()


async def ping_worker(root_ctx: RootContext, request_id: str) -> None:
    worker_config = root_ctx.local_config.proxy_worker
    try:
        async with coordinator_request_context(request_id, root_ctx) as sess:
            await sess.patch(f"/api/worker/{root_ctx.worker_id}")
    except ClientConnectorError as e:
        raise CoordinatorConnectionError(
            extra_data={
                "authority": worker_config.authority,
                "coordinator": str(worker_config.coordinator_endpoint),
            }
        ) from e


async def get_token_data(root_ctx: RootContext, request_id: str, token_id: str) -> Token:
    async with coordinator_request_context(request_id, root_ctx) as sess:
        async with sess.get(f"/api/worker/token/{token_id}") as resp:
            resp.raise_for_status()
            return Token(**(await resp.json()))
