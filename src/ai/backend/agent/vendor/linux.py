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
    async def htcpu_info():
        file_path = os.path.join("/sys/devices/system/cpu/cpu0/topology/thread_siblings_list")
        cpu_count = os.cpu_count()
        num_htSiblings = 0
        try:
            with open(file_path) as siblings:
                htSiblings = len(siblings.read().split(','))
                if htSiblings > 0:
                    num_htSiblings = cpu_count // htSiblings
                    return({'isActive': True, 'num_htcpu': num_htSiblings})
                else:
                    return({'isActive': False, 'num_htcpu': 0})
        except (IOError, OSError) as e:
            raise Exception(
                "{}\nCould not read thread siblings list".format(e))

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
            num_htSiblings = await libnuma.htcpu_info()['num_htcpu']
            try:
                restricted_pid_cpu = os.sched_getaffinity(os.getpid())
                for cpu in list(restricted_pid_cpu):
                    if cpu > num_htSiblings - 1:
                        restricted_pid_cpu.discard(cpu)
                return restricted_pid_cpu
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
