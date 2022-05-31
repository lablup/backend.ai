import ctypes, ctypes.util
import os
import sys

import aiohttp
import aiotools

_numa_supported = False

if sys.platform == 'linux':
    _libnuma_path = ctypes.util.find_library('numa')
    if _libnuma_path:
        _libnuma = ctypes.CDLL(_libnuma_path)
        _numa_supported = True


class libnuma:

    @staticmethod
    def node_of_cpu(core):
        if _numa_supported:
            return int(_libnuma.numa_node_of_cpu(core))
        else:
            return 0

    @staticmethod
    def num_nodes():
        if _numa_supported:
            return int(_libnuma.numa_num_configured_nodes())
        else:
            return 1

    @staticmethod
    @aiotools.lru_cache(maxsize=1)
    async def get_available_cores():
        try:
            # Try to get the # cores allocated to Docker first.
            unix_conn = aiohttp.UnixConnector('/var/run/docker.sock')
            async with aiohttp.ClientSession(connector=unix_conn) as sess:
                async with sess.get('http://docker/info') as resp:
                    data = await resp.json()
                    return {idx for idx in range(data['NCPU'])}
        except aiohttp.ClientError:
            try:
                return os.sched_getaffinity(os.getpid())
            except AttributeError:
                return {idx for idx in range(os.cpu_count())}

    @staticmethod
    async def get_core_topology(limit_cpus=None):
        topo = tuple([] for _ in range(libnuma.num_nodes()))
        for c in (await libnuma.get_available_cores()):
            if limit_cpus is not None and c not in limit_cpus:
                continue
            n = libnuma.node_of_cpu(c)
            topo[n].append(c)
        return topo
