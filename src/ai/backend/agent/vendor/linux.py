import ctypes
import ctypes.util
import logging
import os
import sys
from typing import Iterator

import aiohttp
import aiotools

from ai.backend.common.cgroup import get_cgroup_mount_point
from ai.backend.common.docker import get_docker_connector
from ai.backend.common.logging import BraceStyleAdapter

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]
_numa_supported = False

if sys.platform == "linux":
    _libnuma_path = ctypes.util.find_library("numa")
    if _libnuma_path:
        _libnuma = ctypes.CDLL(_libnuma_path)
        _numa_supported = True


def get_cpus() -> set[int]:
    cpu_count = os.cpu_count()
    if cpu_count is None:
        return {0}
    return {idx for idx in range(cpu_count)}


def parse_cpuset(value: str) -> Iterator[int]:
    if not value:
        raise ValueError("empty cpuset value")
    ranges = value.split(",")
    for r in ranges:
        begin, _, end = r.partition("-")
        if end:
            begin_value = int(begin)
            end_value = int(end)
            if begin_value > end_value:
                raise ValueError(f"invalid range in cpuset: {begin}-{end}")
            yield from range(int(begin), int(end) + 1)
        else:
            yield int(begin)


class libnuma:
    @staticmethod
    def node_of_cpu(core) -> int:
        if _numa_supported:
            return int(_libnuma.numa_node_of_cpu(core))  # type: ignore
        else:
            return 0

    @staticmethod
    def num_nodes() -> int:
        if _numa_supported:
            return int(_libnuma.numa_num_configured_nodes())  # type: ignore
        else:
            return 1

    @staticmethod
    @aiotools.lru_cache(maxsize=1)
    async def get_available_cores() -> set[int]:
        fallback_cpuset_source = "the system cpu count"

        async def read_cgroup_cpuset() -> tuple[set[int], str] | None:
            try:
                connector = get_docker_connector()
                async with aiohttp.ClientSession(connector=connector.connector) as sess:
                    async with sess.get(connector.docker_host / "info") as resp:
                        data = await resp.json()
            except (RuntimeError, aiohttp.ClientError):
                return None
            # Assume cgroup v1 if CgroupVersion key is absent
            if "CgroupVersion" not in data:
                data["CgroupVersion"] = "1"
            driver = data["CgroupDriver"]
            version = data["CgroupVersion"]
            try:
                mount_point = get_cgroup_mount_point(version, "cpuset")
            except RuntimeError:
                return None
            match driver:
                case "cgroupfs":
                    cgroup_parent = "docker"
                case "systemd":
                    cgroup_parent = "system.slice"
                case _:
                    log.warning(
                        "unsupported cgroup driver: {}, falling back to the next cpuset source",
                        driver,
                    )
                    return None
            match version:
                case "1":
                    cpuset_source_name = "cpuset.effective_cpus"
                case "2":
                    cpuset_source_name = "cpuset.cpus.effective"
                case _:
                    log.warning(
                        "unsupported cgroup version: {}, falling back to the next cpuset source",
                        driver,
                    )
                    return None
            docker_cpuset_path = mount_point / cgroup_parent / cpuset_source_name
            log.debug(f"docker_cpuset_path: {docker_cpuset_path}")
            cpuset_source = "the docker cgroup (v{})".format(version)
            try:
                docker_cpuset = docker_cpuset_path.read_text()
                cpuset = {*parse_cpuset(docker_cpuset)}
                return cpuset, cpuset_source
            except (IOError, ValueError):
                log.warning(
                    "failed to parse cgroup cpuset from {}, falling back to the next cpuset source",
                    docker_cpuset_path,
                )
                return None

        async def read_affinity_cpuset() -> tuple[set[int], str] | None:
            try:
                cpuset = os.sched_getaffinity(0)  # type: ignore
                cpuset_source = "the scheduler affinity mask of the agent process"
            except AttributeError:
                return None
            else:
                return cpuset, cpuset_source

        async def read_os_cpus() -> tuple[set[int], str] | None:
            # A fallback implementation from the stdlib
            return get_cpus(), fallback_cpuset_source

        cpuset_source = fallback_cpuset_source
        try:
            match sys.platform:
                case "linux":
                    for reader_func in [
                        # the list of cpuset source to try
                        read_cgroup_cpuset,
                        read_affinity_cpuset,
                        read_os_cpus,
                    ]:
                        result = await reader_func()
                        if result is None:
                            continue
                        cpuset, cpuset_source = result
                        return cpuset
                    else:
                        raise RuntimeError("should not reach here")
                case "darwin" | "win32":
                    try:
                        cpuset_source = "the cpus accessible by the docker service"
                        connector = get_docker_connector()
                        async with aiohttp.ClientSession(connector=connector.connector) as sess:
                            async with sess.get(connector.docker_host / "info") as resp:
                                data = await resp.json()
                                return {idx for idx in range(data["NCPU"])}
                    except (RuntimeError, aiohttp.ClientError):
                        cpuset_source = fallback_cpuset_source
                        return get_cpus()
                case _:
                    return get_cpus()
        finally:
            log.debug("read the available cpuset from {}", cpuset_source)

    @staticmethod
    async def get_core_topology(limit_cpus=None) -> tuple[list[int], ...]:
        topo: tuple[list[int], ...] = tuple([] for _ in range(libnuma.num_nodes()))
        for c in await libnuma.get_available_cores():
            if limit_cpus is not None and c not in limit_cpus:
                continue
            n = libnuma.node_of_cpu(c)
            topo[n].append(c)
        return topo
