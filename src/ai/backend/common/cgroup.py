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
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import aiohttp

from .docker import get_docker_connector
from .logging import BraceStyleAdapter
from .types import PID, ContainerId

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@dataclass
class CgroupVersion:
    version: Literal["v1"] | Literal["v2"]
    driver: Literal["systemd"] | Literal["cgroupfs"]


async def get_docker_cgroup_version() -> CgroupVersion:
    connector = get_docker_connector()
    async with aiohttp.ClientSession(connector=connector.connector) as sess:
        async with sess.get(connector.docker_host / "info") as resp:
            data = await resp.json()
            return CgroupVersion(data["CgroupVersion"], data["CgroupDriver"])


def get_cgroup_mount_point(version: str, controller: str) -> Path:
    for line in Path("/proc/mounts").read_text().splitlines():
        device, mount_point, fstype, options, _ = line.split(" ", 4)
        match version:
            case "1":
                if fstype == "cgroup":
                    if controller in options.split(","):
                        return Path(mount_point)
            case "2":
                if fstype == "cgroup2":
                    return Path(mount_point)
    raise RuntimeError("could not find the cgroup mount point")


def get_cgroup_controller_id(controller: str) -> str:
    # example data
    # cpu <tab> 1 <tab> ...
    # cpuacct <tab> 1 <tab> ...
    for line in Path("/proc/cgroups").read_text().splitlines():
        name, id, _ = line.split("\t", 2)
        if name == controller:
            return id
    raise RuntimeError(f"could not find the cgroup controller {controller}")


def get_cgroup_of_pid(controller: str, pid: PID) -> str:
    # example data
    # 1:cpu,cpuacct:/<cgroup>
    controller_id = get_cgroup_controller_id(controller)
    for line in Path(f"/proc/{pid}/cgroup").read_text().splitlines():
        id, name, cgroup = line.split(":", 2)
        if id == controller_id:
            return cgroup.removeprefix("/")
    raise RuntimeError(f"could not find the cgroup of PID {pid}")


def get_container_id_of_cgroup(cgroup: str) -> Optional[str]:
    # cgroupfs driver: docker/<id>
    cgroupfs_prefix = "docker/"
    if cgroup.startswith(cgroupfs_prefix):
        return cgroup.removeprefix(cgroupfs_prefix)
    # systemd driver: system.slice/docker-<id>.scope
    systemd_prefix = "system.slice/docker-"
    systemd_suffix = ".scope"
    if cgroup.startswith(systemd_prefix) and cgroup.endswith(systemd_suffix):
        return cgroup.removeprefix(systemd_prefix).removesuffix(systemd_suffix)
    return None


async def get_container_pids(cid: ContainerId) -> list[int]:
    cgroup_version = await get_docker_cgroup_version()
    log.debug("Cgroup version: {}, {}", cgroup_version.version, cgroup_version.driver)
    match (cgroup_version.version, cgroup_version.driver):
        case ("2", "systemd"):
            tasks_path = Path(f"/sys/fs/cgroup/system.slice/docker-{cid}.scope/cgroup.procs")
        case ("2", "cgroupfs"):
            tasks_path = Path(f"/sys/fs/cgroup/docker/{cid}/cgroup.procs")
        case ("1", _):
            tasks_path = Path(f"/sys/fs/cgroup/pids/docker/{cid}/tasks")
        case _:
            raise RuntimeError("Should not reach here")
    tasks = await asyncio.get_running_loop().run_in_executor(None, tasks_path.read_text)
    return [*map(int, tasks.splitlines())]
