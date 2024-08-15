import asyncio
import hashlib
import io
import ipaddress
import json
import logging
import platform
import re
from decimal import Decimal
from pathlib import Path
from typing import (
    Any,
    AsyncContextManager,
    List,
    Mapping,
    MutableMapping,
    NamedTuple,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)
from uuid import UUID

import aiodocker
import trafaret as t
from aiodocker.docker import DockerContainer
from typing_extensions import Final

from ai.backend.common import identity
from ai.backend.common.cgroup import (
    get_cgroup_of_pid,
    get_container_id_of_cgroup,
    get_container_pids,
)
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import PID, ContainerId, ContainerPID, HostPID, KernelId
from ai.backend.common.utils import current_loop

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

IPNetwork = Union[ipaddress.IPv4Network, ipaddress.IPv6Network]
IPAddress = Union[ipaddress.IPv4Address, ipaddress.IPv6Address]

InOtherContainerPID: Final = ContainerPID(PID(-2))
NotContainerPID: Final = ContainerPID(PID(-1))
NotHostPID: Final = HostPID(PID(-1))


class SupportsAsyncClose(Protocol):
    async def close(self) -> None: ...


_SupportsAsyncCloseT = TypeVar("_SupportsAsyncCloseT", bound=SupportsAsyncClose)


class closing_async(AsyncContextManager[_SupportsAsyncCloseT]):
    """
    contextlib.closing calls close(), and aiotools.aclosing() calls aclose().
    This context manager calls close() as a coroutine.
    """

    def __init__(self, obj: _SupportsAsyncCloseT) -> None:
        self.obj = obj

    async def __aenter__(self) -> _SupportsAsyncCloseT:
        return self.obj

    async def __aexit__(self, *exc_info) -> None:
        await self.obj.close()


def generate_local_instance_id(hint: str) -> str:
    return hashlib.md5(hint.encode("utf-8")).hexdigest()[:12]


def get_arch_name() -> str:
    ret = platform.machine().lower()
    aliases = {
        "arm64": "aarch64",  # macOS with LLVM
        "amd64": "x86_64",  # Windows/Linux
        "x64": "x86_64",  # Windows
        "x32": "x86",  # Windows
        "i686": "x86",  # Windows
    }
    return aliases.get(ret, ret)


def update_nested_dict(dest: MutableMapping, additions: Mapping) -> None:
    for k, v in additions.items():
        if k not in dest:
            dest[k] = v
        else:
            if isinstance(dest[k], MutableMapping):
                assert isinstance(v, MutableMapping)
                update_nested_dict(dest[k], v)
            elif isinstance(dest[k], List):
                assert isinstance(v, List)
                dest[k].extend(v)
            else:
                dest[k] = v


def numeric_list(s: str) -> List[int]:
    return [int(p) for p in s.split()]


def remove_exponent(num: Decimal) -> Decimal:
    return num.quantize(Decimal(1)) if num == num.to_integral() else num.normalize()


@overload
def read_sysfs(path: Union[str, Path], type_: Type[bool], default: bool) -> bool: ...


@overload
def read_sysfs(path: Union[str, Path], type_: Type[int], default: int) -> int: ...


@overload
def read_sysfs(path: Union[str, Path], type_: Type[float], default: float) -> float: ...


@overload
def read_sysfs(path: Union[str, Path], type_: Type[str], default: str) -> str: ...


def read_sysfs(path: Union[str, Path], type_: Type[Any], default: Any = None) -> Any:
    def_vals: Mapping[Any, Any] = {
        bool: False,
        int: 0,
        float: 0.0,
        str: "",
    }
    if type_ not in def_vals:
        raise TypeError("unsupported conversion type from sysfs content")
    if default is None:
        default = def_vals[type_]
    try:
        raw_str = Path(path).read_text().strip()
        if type_ is bool:
            return t.ToBool().check(raw_str)
        else:
            return type_(raw_str)
    except IOError:
        return default


async def read_tail(path: Path, nbytes: int) -> bytes:
    file_size = path.stat().st_size

    def _read_tail() -> bytes:
        with open(path, "rb") as f:
            f.seek(max(file_size - nbytes, 0), io.SEEK_SET)
            return f.read(nbytes)

    loop = current_loop()
    return await loop.run_in_executor(None, _read_tail)


async def get_kernel_id_from_container(val: Union[str, DockerContainer]) -> Optional[KernelId]:
    if isinstance(val, DockerContainer):
        if "Name" not in val._container:
            await val.show()
        name = val["Name"]
    elif isinstance(val, str):
        name = val
    name = name.lstrip("/")
    if not name.startswith("kernel."):
        return None
    try:
        return KernelId(UUID(name.rsplit(".", 2)[-1]))
    except (IndexError, ValueError):
        return None


async def get_subnet_ip(etcd: AsyncEtcd, network: str, fallback_addr: str = "0.0.0.0") -> str:
    raw_subnet = await etcd.get(f"config/network/subnet/{network}")
    if raw_subnet is None:
        addr = fallback_addr
    else:
        subnet = ipaddress.ip_network(raw_subnet)
        if subnet.prefixlen == 0:
            addr = fallback_addr
        else:
            local_ipaddrs = [*identity.fetch_local_ipaddrs(subnet)]
            log.debug("get_subnet_ip(): subnet {} candidates: {}", subnet, local_ipaddrs)
            if local_ipaddrs:
                addr = str(local_ipaddrs[0])
            else:
                addr = fallback_addr
    return addr


class ProcessInfo(NamedTuple):
    pid: int
    command: str


async def get_host_process_table(
    docker: aiodocker.Docker,
    container_id: str,
) -> List[ProcessInfo]:
    result = await docker._query_json(f"containers/{container_id}/top", method="GET")
    procs = result["Processes"]
    return [ProcessInfo(int(x[1]), x[7]) for x in procs]


async def get_container_process_table(
    docker: aiodocker.Docker,
    container_id: str,
) -> List[ProcessInfo]:
    # Get process table from inside container (execute 'ps -aux' command from container).
    # Filter processes which have exactly the same COMMAND like above.
    result = await docker._query_json(
        f"containers/{container_id}/exec",
        method="POST",
        data={
            "AttachStdin": False,
            "AttachStdout": True,
            "AttachStderr": True,
            "Cmd": ["ps", "aux"],
        },
    )
    exec_id = result["Id"]
    async with docker._query(
        f"exec/{exec_id}/start",
        method="POST",
        headers={"content-type": "application/json"},
        data=json.dumps({
            "Stream": False,  # get response immediately
            "Detach": False,
            "Tty": False,
        }),
    ) as resp:
        result = await resp.read()
        result = result.decode("latin-1").strip().split("\n")
    result = list(map(lambda x: x.split(), result))
    head = result[0]
    procs = result[1:]
    pid_idx, cmd_idx = head.index("PID"), head.index("COMMAND")
    return [ProcessInfo(int(r[pid_idx]), " ".join(r[cmd_idx:])) for r in procs]


async def host_pid_to_container_pid(container_id: str, host_pid: HostPID) -> ContainerPID:
    kernel_ver = Path("/proc/version").read_text()
    if m := re.match(r"Linux version (\d+)\.(\d+)\..*", kernel_ver):  # noqa
        kernel_ver_tuple: Tuple[str, str] = m.groups()  # type: ignore
        if kernel_ver_tuple < ("4", "1"):
            # TODO: this should be deprecated when the minimun supported Linux kernel will be 4.1.
            #
            # In CentOs 7, NSPid is not accesible since it is supported from Linux kernel >=4.1.
            # We provide alternative, although messy, way for older Linux kernels. Below describes
            # the logic briefly:
            #   * Obtain information on all the processes inside the target container,
            #     which contains host PID, by docker top API (containers/<container-id>/top).
            #     - Get the COMMAND of the target process (by using host_pid).
            #     - Filter host processes which have the exact same COMMAND.
            #   * Obtain information on all the processes inside the target container,
            #     which contains container PID, by executing "ps -aux" command from inside the container.
            #     - Filter container processes which have the exact same COMMAND.
            #   * Get the index of the target process from the host process table.
            #   * Use the index to get the target process from the container process table, and get PID.
            #     - Since docker top and ps -aux both displays processes in the order of PID, we
            #       can safely assume that the order of the processes from both tables are the same.
            #
            # Example host and container process table:
            #
            # [
            #   ['devops', '15454', '12942', '99', '15:36', 'pts/1', '00:00:08', 'python mnist.py'],
            #   ... (processes with the same COMMAND)
            # ]
            #
            # [
            #   ['work', '227', '121', '4.6', '22408680', '1525428', 'pts/1', 'Rl+', '06:36', '0:08',
            #    'python', 'mnist.py'],
            #   ... (processes with the same COMMAND)
            # ]
            try:
                docker = aiodocker.Docker()
                # Get process table from host (docker top information). Filter processes which have
                # exactly the same COMMAND as with target host process.
                host_procs = await get_host_process_table(docker, container_id)
                cmd = [x.command for x in host_procs if x.pid == int(host_pid)][0]
                host_pids = [x.pid for x in host_procs if x.command == cmd]

                # When there are multiple processes which have the same COMMAND, just get the index of
                # the target host process and apply it with the container table. Since ps and docker top
                # both displays processes ordered by PID, we can expect those two tables have same
                # order of processes.
                process_idx = host_pids.index(int(host_pid))

                container_procs = await get_container_process_table(docker, container_id)
                container_pids = [x.pid for x in container_procs if x.command == cmd]

                container_pid = ContainerPID(PID(container_pids[process_idx]))
                log.debug("host pid {} is mapped to container pid {}", host_pid, container_pid)
                return container_pid
            except asyncio.CancelledError:
                raise
            except (IndexError, KeyError, aiodocker.exceptions.DockerError):
                return NotContainerPID
            finally:
                await docker.close()

    try:
        cgroup = get_cgroup_of_pid("pids", host_pid)
        cgroup_container_id = get_container_id_of_cgroup(cgroup)
        if cgroup_container_id is None:
            return NotContainerPID
        if cgroup_container_id == container_id:
            for line in Path(f"/proc/{host_pid}/status").read_text().splitlines():
                key, value = line.split(":\t", 1)
                if key == "NSpid":
                    pid = value.split()[1]
                    return ContainerPID(PID(int(pid)))
        return InOtherContainerPID
    except OSError:
        return NotContainerPID


async def container_pid_to_host_pid(container_id: str, container_pid: ContainerPID) -> HostPID:
    kernel_ver = Path("/proc/version").read_text()
    if m := re.match(r"Linux version (\d+)\.(\d+)\..*", kernel_ver):  # noqa
        kernel_ver_tuple: Tuple[str, str] = m.groups()  # type: ignore
        if kernel_ver_tuple < ("4", "1"):
            # reverse implementation of host_pid_to_container_pid().
            try:
                docker = aiodocker.Docker()
                container_procs = await get_container_process_table(docker, container_id)
                cmd = [x.command for x in container_procs if x.pid == int(container_pid)][0]
                container_pids = [x.pid for x in container_procs if x.command == cmd]
                process_idx = container_pids.index(int(container_pid))

                host_procs = await get_host_process_table(docker, container_id)
                host_pids = [x.pid for x in host_procs if x.command == cmd]

                host_pid = HostPID(PID(host_pids[process_idx]))
                log.debug("container pid {} is mapped to host pid {}", container_pid, host_pid)
                return host_pid
            except asyncio.CancelledError:
                raise
            except (IndexError, KeyError, aiodocker.exceptions.DockerError):
                return NotHostPID
            finally:
                await docker.close()

    try:
        cgtasks = await get_container_pids(ContainerId(container_id))
        for pid in cgtasks:
            proc_path = Path(f"/proc/{pid}/status")
            proc_status = {
                k: v
                for k, v in map(lambda line: line.split(":\t"), proc_path.read_text().splitlines())
            }
            nspids = proc_status["NSpid"].split()
            if nspids[1] == str(container_pid):
                return HostPID(PID(pid))
        return NotHostPID
    except (ValueError, KeyError, IOError):
        return NotHostPID
