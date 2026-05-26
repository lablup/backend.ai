"""
Backend.AI swarm-network-daemon — out-of-process docker swarm overlay
network manager. Talks to the node's docker daemon via /var/run/docker.sock
(hostPath mount in k8s).

Endpoints (all JSON, auth via X-Auth-Token header when configured):
    GET    /health                -> 200 { "status": "ok", "swarm": "active|inactive" }
    POST   /networks              -> 200 { "network_id": "...", "options": {...} }
        body: { "identifier"?: "...", "options"?: {...} }
    GET    /networks/{name}       -> 200 { "network_id": "...", "options": {...} } | 404
    DELETE /networks/{name}       -> 204 | 404

Environment:
    BIND_ADDR        default 0.0.0.0
    BIND_PORT        default 7700
    AUTH_TOKEN       default '' (empty disables auth)
    DOCKER_HOST      default 'unix:///var/run/docker.sock'
    MTU              default 1500
    NETWORK_PREFIX   default 'bai-multinode-'
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from http import HTTPStatus

import aiodocker
from aiodocker.exceptions import DockerError
from aiohttp import web

log = logging.getLogger("swarm-network-daemon")


BIND_ADDR = os.environ.get("BIND_ADDR", "0.0.0.0")
BIND_PORT = int(os.environ.get("BIND_PORT", "7700"))
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "")
MTU = int(os.environ.get("MTU", "1500"))
NETWORK_PREFIX = os.environ.get("NETWORK_PREFIX", "bai-multinode-")


@web.middleware
async def auth_middleware(request: web.Request, handler):
    if AUTH_TOKEN and request.path != "/health":
        token = request.headers.get("X-Auth-Token", "")
        if token != AUTH_TOKEN:
            return web.json_response(
                {"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED
            )
    return await handler(request)


async def health(request: web.Request) -> web.Response:
    docker = request.app["docker"]
    info = await docker.system.info()
    swarm_state = info.get("Swarm", {}).get("LocalNodeState", "inactive")
    return web.json_response({"status": "ok", "swarm": swarm_state})


async def create_network(request: web.Request) -> web.Response:
    docker: aiodocker.Docker = request.app["docker"]
    payload = await request.json() if request.body_exists else {}
    identifier = payload.get("identifier") or f"{uuid.uuid4()}-nw"
    network_name = f"{NETWORK_PREFIX}{identifier}"

    # Idempotent: if already exists, return current info.
    try:
        item = await docker.networks.get(network_name)
        info = await item.show()
        return web.json_response({
            "network_id": network_name,
            "options": {
                "mode": info["Driver"],
                "network_name": network_name,
                "network_id": info["Id"],
            },
        })
    except DockerError as e:
        if e.status != HTTPStatus.NOT_FOUND:
            raise

    create_opts = {
        "Name": network_name,
        "Driver": "overlay",
        "Attachable": True,
        "Labels": {"ai.backend.cluster-network": "1"},
        "Options": {"com.docker.network.driver.mtu": str(MTU)} if MTU else {},
    }
    result = await docker.networks.create(create_opts)
    return web.json_response({
        "network_id": network_name,
        "options": {
            "mode": "overlay",
            "network_name": network_name,
            "network_id": result.id,
        },
    })


async def get_network(request: web.Request) -> web.Response:
    docker: aiodocker.Docker = request.app["docker"]
    name = request.match_info["name"]
    try:
        item = await docker.networks.get(name)
        info = await item.show()
        return web.json_response({
            "network_id": name,
            "options": {
                "mode": info["Driver"],
                "network_name": name,
                "network_id": info["Id"],
            },
        })
    except DockerError as e:
        if e.status == HTTPStatus.NOT_FOUND:
            return web.json_response({"error": "not_found"}, status=404)
        raise


async def destroy_network(request: web.Request) -> web.Response:
    docker: aiodocker.Docker = request.app["docker"]
    name = request.match_info["name"]
    try:
        # Same 2-second grace as OverlayNetworkPlugin — give detaching
        # containers time to exit before tearing down the network.
        await asyncio.sleep(2.0)
        network = await docker.networks.get(name)
        await network.delete()
        return web.Response(status=204)
    except DockerError as e:
        if e.status == HTTPStatus.NOT_FOUND:
            return web.Response(status=404)
        raise


async def on_startup(app: web.Application) -> None:
    app["docker"] = aiodocker.Docker()


async def on_cleanup(app: web.Application) -> None:
    await app["docker"].close()


def create_app() -> web.Application:
    app = web.Application(middlewares=[auth_middleware])
    app.router.add_get("/health", health)
    app.router.add_post("/networks", create_network)
    app.router.add_get("/networks/{name}", get_network)
    app.router.add_delete("/networks/{name}", destroy_network)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    log.info("swarm-network-daemon listening on %s:%s (auth=%s)",
             BIND_ADDR, BIND_PORT, "on" if AUTH_TOKEN else "off")
    web.run_app(create_app(), host=BIND_ADDR, port=BIND_PORT, access_log=None)
