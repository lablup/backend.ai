import asyncio
import functools
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence, TypeVar


async def host_pid_to_container_pid(container_id: str, host_pid: int) -> int:
    try:
        for p in Path("/sys/fs/cgroup/pids/docker").iterdir():
            if not p.is_dir():
                continue
            tasks_path = p / "tasks"
            cgtasks = [*map(int, tasks_path.read_text().splitlines())]
            if host_pid not in cgtasks:
                continue
            if p.name == container_id:
                proc_path = Path(f"/proc/{host_pid}/status")
                proc_status = {
                    k: v
                    for k, v in map(
                        lambda line: line.split(":\t"), proc_path.read_text().splitlines()
                    )
                }
                nspids = [*map(int, proc_status["NSpid"].split())]
                return nspids[1]  # in the given container
            return -2  # in other container
        return -1  # in host
    except (ValueError, KeyError, IOError):
        return -1  # in host


T = TypeVar("T")


async def run_sync(
    closure: Callable[..., T], *args: Sequence[Any], **kwargs: Mapping[Any, Any]
) -> T:
    return await asyncio.get_running_loop().run_in_executor(
        None,
        functools.partial(closure, *args, **kwargs),
    )
