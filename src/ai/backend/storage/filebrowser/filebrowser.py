from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, List, Mapping, NamedTuple, Type
from uuid import UUID

import aiodocker
import pkg_resources

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.utils import closing_async
from ai.backend.storage.abc import AbstractVolume
from ai.backend.storage.context import Context
from ai.backend.storage.utils import get_available_port
from ai.backend.storage.vfs import BaseVolume

from .config_browser_app import prepare_filebrowser_app_config
from .database import FilebrowserTrackerDB

logger = logging.getLogger(__name__)
log = BraceStyleAdapter(logging.getLogger(__name__))

BACKENDS: Mapping[str, Type[AbstractVolume]] = {
    "vfs": BaseVolume,
}


__all__ = (
    "create_or_update",
    "destroy_container",
    "get_container_by_id",
    "get_filebrowsers",
    "get_network_stats",
    "check_container_existance",
)


class FileBrowserResult(NamedTuple):
    container_id: str
    port: int
    token: str


class NetworkStatsResult(NamedTuple):
    rx_bytes: int
    tx_bytes: int


async def create_or_update(
    ctx: Context,
    host: str,
    vfolders: list[dict],
) -> FileBrowserResult:
    image = ctx.local_config["filebrowser"]["image"]
    service_ip = ctx.local_config["filebrowser"]["service_ip"]
    service_port = ctx.local_config["filebrowser"]["service_port"]
    max_containers = ctx.local_config["filebrowser"]["max_containers"]
    user_id = ctx.local_config["filebrowser"]["user_id"]
    group_id = ctx.local_config["filebrowser"]["group_id"]
    cpu_count = ctx.local_config["filebrowser"]["max_cpu"]
    memory = ctx.local_config["filebrowser"]["max_mem"]
    db_path = ctx.local_config["filebrowser"]["db_path"]
    p = Path(pkg_resources.resource_filename(__name__, ""))
    storage_proxy_root_path_index = p.parts.index("storage")
    settings_path = Path(*p.parts[0 : storage_proxy_root_path_index + 1]) / "filebrowser_app/"
    _, requested_volume = host.split(":", maxsplit=1)
    found_volume = False
    volumes = ctx.local_config["volume"]
    for volume_name in volumes.keys():
        if requested_volume == volume_name:
            volume_cls: Type[AbstractVolume] = BACKENDS[volumes.get(volume_name)["backend"]]
            mount_path = Path(volumes.get(volume_name)["path"])
            volume_obj = volume_cls(
                local_config=ctx.local_config,
                mount_path=mount_path,
                fsprefix=None,
                options={},
            )
            found_volume = True
            break
    if not found_volume:
        raise ValueError(
            f"Requested volume '{requested_volume}' does not exist in the configuration."
        )

    port_range = ctx.local_config["filebrowser"]["port_range"].split("-")
    service_port = get_available_port(port_range)
    running_docker_containers = await get_filebrowsers()
    if len(running_docker_containers) >= max_containers:
        log.error("Can't create new container. Number of containers exceed the maximum limit.")
        return FileBrowserResult("0", 0, "0")
    await prepare_filebrowser_app_config(
        settings_path, service_port, ctx.local_config["filebrowser"]["filebrowser_key"]
    )
    async with closing_async(aiodocker.Docker()) as docker:
        config = {
            "Cmd": [
                "/filebrowser_app/start.sh",
                f"{user_id}",
                f"{group_id}",
                f"{service_port}",
            ],
            "ExposedPorts": {
                f"{service_port}/tcp": {},
            },
            "Image": image,
            "HostConfig": {
                "PortBindings": {
                    f"{service_port}/tcp": [
                        {
                            "HostIp": f"{service_ip}",
                            "HostPort": f"{service_port}/tcp",
                        },
                    ],
                },
                "CpuCount": cpu_count,
                "Memory": memory,
                "Mounts": [
                    {
                        "Target": "/filebrowser_app/",
                        "Source": f"{settings_path}",
                        "Type": "bind",
                    },
                ],
            },
        }
        for vfolder in vfolders:
            filebrowser_mount_path = str(
                volume_obj.mangle_vfpath(UUID(vfolder["vfid"])),
            )
            config["HostConfig"]["Mounts"].append(
                {
                    "Target": f"/data/{vfolder['name']}",
                    "Source": filebrowser_mount_path,
                    "Type": "bind",
                },
            )
        container_name = f"ai.backend.container-filebrowser-{service_port}"
        container = await docker.containers.create_or_replace(
            config=config,
            name=container_name,
        )
        container_id = container._id
        await container.start()
    tracker_db = await FilebrowserTrackerDB.create(db_path)
    await tracker_db.insert_new_container(
        container_id,
        container_name,
        service_ip,
        service_port,
        config,
        "RUNNING",
        str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    return FileBrowserResult(service_ip, service_port, container_id)


async def recreate_container(container_name: str, config: dict[str, Any]) -> None:
    async with closing_async(aiodocker.Docker()) as docker:
        try:
            docker = aiodocker.Docker()
            container = await docker.containers.create_or_replace(
                config=config,
                name=container_name,
            )
            await container.start()
        except aiodocker.exceptions.DockerError as e:
            logger.error(f"Failure to recreate container: {container_name}. Error: {e}")


async def check_container_existance(container_id: str) -> bool:
    async with closing_async(aiodocker.Docker()) as docker:
        for container in await docker.containers.list():
            if container._id == container_id:
                return True
        return False


async def close_all_filebrowser_containers(ctx) -> None:
    db_path = ctx.local_config["filebrowser"]["db_path"]
    tracker_db = await FilebrowserTrackerDB.create(db_path)
    async with closing_async(aiodocker.Docker()) as docker:
        for container in await docker.containers.list(all=True):
            if "ai.backend.container-filebrowser" in container._container["Names"][0]:
                await container.stop()
                await container.delete(force=True)
                await tracker_db.delete_container_record(container._id)


async def destroy_container(ctx: Context, container_id: str) -> None:
    db_path = ctx.local_config["filebrowser"]["db_path"]
    tracker_db = await FilebrowserTrackerDB.create(db_path)
    async with closing_async(aiodocker.Docker()) as docker:
        if await check_container_existance(container_id) is True:
            container = aiodocker.docker.DockerContainers(docker).container(
                container_id=container_id,
            )
            try:
                await container.stop()
                await container.delete(force=True)
                await tracker_db.delete_container_record(container_id)
            except aiodocker.exceptions.DockerError as e:
                log.error(f"Failure to destroy container {container_id[0:7]} ", e)


async def get_container_by_id(container_id: str) -> Any:
    async with closing_async(aiodocker.Docker()) as docker:
        container = aiodocker.docker.DockerContainers(docker).container(
            container_id=container_id,
        )
    return container


async def get_filebrowsers() -> List[str]:
    container_list = []
    async with closing_async(aiodocker.Docker()) as docker:
        containers = await aiodocker.docker.DockerContainers(docker).list(all=True)
        for container in containers:
            stats = await container.stats(stream=False)
            name = stats[0]["name"]
            cnt_id = stats[0]["id"]
            if "ai.backend.container-filebrowser" in name:
                container_list.append(cnt_id)
    return container_list


async def get_network_stats(container_id: str) -> NetworkStatsResult:
    async with closing_async(aiodocker.Docker()) as docker:
        try:
            container = aiodocker.docker.DockerContainers(docker).container(
                container_id=container_id,
            )
            if container in await docker.containers.list():
                stats = await container.stats(stream=False)
            else:
                return NetworkStatsResult(0, 0)
        except aiodocker.exceptions.DockerError as e:
            log.error(f"Failure to get network stats for container {container_id[0:7]}, {e} ")
            return NetworkStatsResult(0, 0)
    return NetworkStatsResult(
        int(stats[0]["networks"]["eth0"]["rx_bytes"]), int(stats[0]["networks"]["eth0"]["tx_bytes"])
    )
