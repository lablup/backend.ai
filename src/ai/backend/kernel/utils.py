import asyncio
import os
from pathlib import Path
from typing import Final

__all__ = (
    "current_loop",
    "find_executable",
    "safe_close_task",
    "wait_local_port_open",
)


if hasattr(asyncio, "get_running_loop"):
    current_loop = asyncio.get_running_loop  # type: ignore  # noqa
else:
    current_loop = asyncio.get_event_loop  # type: ignore  # noqa

CLOCK_TICK: Final = os.sysconf("SC_CLK_TCK")


def find_executable(*paths):
    """
    Find the first executable regular file in the given list of paths.
    """
    for path in paths:
        if isinstance(path, (str, bytes)):
            path = Path(path)
        if not path.exists():
            continue
        for child in path.iterdir():
            if child.is_file() and child.stat().st_mode & 0o100 != 0:
                return child
    return None


async def safe_close_task(task):
    if task is not None and not task.done():
        task.cancel()
        await task


async def wait_local_port_open(port):
    while True:
        try:
            async with asyncio.timeout(10.0):
                reader, writer = await asyncio.open_connection("127.0.0.1", port)
        except ConnectionRefusedError:
            await asyncio.sleep(0.1)
            continue
        except asyncio.TimeoutError:
            raise
        except Exception:
            raise
        else:
            writer.close()
            if hasattr(writer, "wait_closed"):
                await writer.wait_closed()
            break


def scan_proc_stats() -> dict[int, dict]:
    pid_set = dict()
    for p in Path("/proc").iterdir():
        if p.name.isdigit():
            pid = int(p.name)
            stat = parse_proc_stat(pid)
            pid_set[pid] = stat
    return pid_set


def parse_proc_stat(pid):
    data = Path(f"/proc/{pid}/stat").read_bytes()
    name_begin = data.find(b"(")
    name_end = data.rfind(b")")
    name = data[name_begin + 1 : name_end]
    fields = data[name_end + 2 :].split()
    # Interpretation of status
    #  R  Running
    #  S  Sleeping in an interruptible wait
    #  D  Waiting in uninterruptible disk sleep
    #  Z  Zombie
    #  T  Stopped (on a signal) or (before Linux 2.6.33) trace stopped
    #  t  Tracing stop (Linux 2.6.33 onward)
    #  X  Dead (from Linux 2.6.0 onward)
    stat = {
        "name": name,
        "cmdline": Path(f"/proc/{pid}/cmdline").read_bytes(),
        "status": fields[0],
        "ppid": int(fields[1]),
        "tty": int(fields[4]),
        "utime": float(fields[11]) / CLOCK_TICK,
        "stime": float(fields[12]) / CLOCK_TICK,
        "starttime": float(fields[19]) / CLOCK_TICK,
        "vsize": int(fields[20]),  # bytes
        "rss": int(fields[21]),  # num pages
    }
    return stat
