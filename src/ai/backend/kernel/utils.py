import asyncio
from pathlib import Path

from async_timeout import timeout

__all__ = (
    'current_loop',
    'find_executable',
    'safe_close_task',
    'wait_local_port_open',
)


if hasattr(asyncio, 'get_running_loop'):
    current_loop = asyncio.get_running_loop  # type: ignore  # noqa
else:
    current_loop = asyncio.get_event_loop    # type: ignore  # noqa


def find_executable(*paths):
    '''
    Find the first executable regular file in the given list of paths.
    '''
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
            with timeout(10.0):
                reader, writer = await asyncio.open_connection('127.0.0.1', port)
        except ConnectionRefusedError:
            await asyncio.sleep(0.1)
            continue
        except asyncio.TimeoutError:
            raise
        except Exception:
            raise
        else:
            writer.close()
            if hasattr(writer, 'wait_closed'):
                await writer.wait_closed()
            break
