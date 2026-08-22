# Relevant Linux kernel documentations
#
# For /proc filesystem, see
# https://docs.kernel.org/filesystems/proc.html
#
# For cgroup v1, see
# https://docs.kernel.org/admin-guide/cgroup-v1/
#
# For cgroup v2, see
# https://docs.kernel.org/admin-guide/cgroup-v2.html

import asyncio
import enum
import logging
import re
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Final, Literal, override

import aiohttp
from aiohttp import web

from ai.backend.logging import BraceStyleAdapter

from .docker import get_docker_connector
from .exception import (
    BackendAIError,
    ErrorCode,
    ErrorDetail,
    ErrorDomain,
    ErrorOperation,
)
from .types import PID, ContainerId

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# Leaf cgroups that container runtimes may interpose between the container scope and
# its processes. They carry no container identity of their own.
_CGROUP_SUBTREE_NAMES: Final[frozenset[str]] = frozenset({"container", "conmon", "supervisor"})
_CONTAINER_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(?:docker-|libpod-payload-|libpod-|crio-)?(?P<id>[0-9a-f]{12,64})(?:\.scope)?$"
)


class CgroupController(enum.StrEnum):
    """A cgroup resource controller, as named in /proc/cgroups and /proc/mounts."""

    CPUACCT = "cpuacct"
    CPUSET = "cpuset"
    MEMORY = "memory"
    BLKIO = "blkio"
    PIDS = "pids"


class CgroupResolutionFailed(BackendAIError, web.HTTPInternalServerError):
    """Raised when the cgroup of a process or a container cannot be determined."""

    error_type = "https://api.backend.ai/probs/cgroup-resolution-failed"
    error_title = "Failed to resolve the cgroup."

    @override
    def error_code(self) -> ErrorCode:
        return ErrorCode(
            domain=ErrorDomain.AGENT,
            operation=ErrorOperation.READ,
            error_detail=ErrorDetail.NOT_FOUND,
        )


@dataclass
class CgroupVersion:
    version: Literal["1"] | Literal["2"]
    driver: Literal["systemd"] | Literal["cgroupfs"]


async def get_docker_cgroup_version() -> CgroupVersion:
    connector = get_docker_connector()
    async with aiohttp.ClientSession(connector=connector.connector) as sess:
        async with sess.get(connector.docker_host / "info") as resp:
            data = await resp.json()
            return CgroupVersion(data["CgroupVersion"], data["CgroupDriver"])


def get_cgroup_mount_point(version: str, controller: CgroupController) -> Path:
    for line in Path("/proc/mounts").read_text().splitlines():
        device, mount_point, fstype, options, _ = line.split(" ", 4)
        match version:
            case "1":
                if fstype == "cgroup":
                    if controller.value in options.split(","):
                        return Path(mount_point)
            case "2":
                if fstype == "cgroup2":
                    return Path(mount_point)
    raise CgroupResolutionFailed("could not find the cgroup mount point")


def get_cgroup_controller_id(controller: CgroupController) -> str:
    # example data
    # cpu <tab> 1 <tab> ...
    # cpuacct <tab> 1 <tab> ...
    for line in Path("/proc/cgroups").read_text().splitlines():
        name, id, _ = line.split("\t", 2)
        if name == controller.value:
            return id
    raise CgroupResolutionFailed(f"could not find the cgroup controller {controller}")


def get_cgroup_of_pid(controller: CgroupController, pid: PID) -> str:
    # example data
    # 1:cpu,cpuacct:/<cgroup>
    controller_id = get_cgroup_controller_id(controller)
    for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines():
        id, name, cgroup = line.split(":", 2)
        if id == controller_id:
            return cgroup.removeprefix("/")
    raise CgroupResolutionFailed(f"could not find the cgroup of PID {pid}")


def get_container_id_of_cgroup(cgroup: str) -> str | None:
    # cgroupfs driver: docker/<id>
    # systemd driver: system.slice/docker-<id>.scope
    # podman: machine.slice/libpod-<id>.scope, optionally with a /container leaf
    # podman with split cgroups: <parent>/libpod-payload-<id>
    segments = [segment for segment in cgroup.strip("/").split("/") if segment]
    while segments and segments[-1] in _CGROUP_SUBTREE_NAMES:
        segments.pop()
    if not segments:
        return None
    if (matched := _CONTAINER_ID_PATTERN.match(segments[-1])) is None:
        return None
    return matched.group("id")


async def get_container_main_pid(cid: ContainerId) -> PID:
    connector = get_docker_connector()
    async with aiohttp.ClientSession(connector=connector.connector) as sess:
        async with sess.get(connector.docker_host / f"containers/{cid}/json") as resp:
            if resp.status != HTTPStatus.OK:
                # The container may have been removed since the caller observed it.
                raise CgroupResolutionFailed(
                    f"could not inspect container {cid} (HTTP {resp.status})"
                )
            data = await resp.json()
    state = data.get("State")
    if state is None or not state.get("Pid"):
        raise CgroupResolutionFailed(f"container {cid} has no running process")
    return PID(state["Pid"])


def get_cgroup_path_of_pid(version: str, controller: CgroupController, pid: PID) -> Path:
    return get_cgroup_mount_point(version, controller) / get_cgroup_of_pid(controller, pid)


async def get_container_cgroup_path(
    version: str, controller: CgroupController, cid: ContainerId
) -> Path:
    """
    Resolve the cgroup path of a container from the cgroup its main process actually
    belongs to, instead of assembling a runtime-specific path.
    """
    pid = await get_container_main_pid(cid)
    return get_cgroup_path_of_pid(version, controller, pid)


async def get_container_pids(cid: ContainerId) -> list[int]:
    cgroup_version = await get_docker_cgroup_version()
    log.debug("Cgroup version: {}, {}", cgroup_version.version, cgroup_version.driver)
    cgroup_path = await get_container_cgroup_path(
        cgroup_version.version, CgroupController.PIDS, cid
    )
    tasks_path = cgroup_path / ("cgroup.procs" if cgroup_version.version == "2" else "tasks")
    tasks = await asyncio.get_running_loop().run_in_executor(None, tasks_path.read_text)
    return [*map(int, tasks.splitlines())]
