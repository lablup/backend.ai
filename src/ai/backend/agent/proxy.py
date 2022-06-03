import asyncio
from asyncio import Future
from pathlib import Path
from typing import Set, Tuple

from ai.backend.common.utils import current_loop
import attr


@attr.s(auto_attribs=True, slots=True)
class DomainSocketProxy:
    host_sock_path: Path
    host_proxy_path: Path
    proxy_server: asyncio.AbstractServer


async def proxy_connection(upper_sock_path: Path,
                           down_reader: asyncio.StreamReader,
                           down_writer: asyncio.StreamWriter) -> None:

    up_reader, up_writer = await asyncio.open_unix_connection(str(upper_sock_path))

    async def _downstream():
        try:
            while True:
                data = await up_reader.read(4096)
                if not data:
                    break
                down_writer.write(data)
                await down_writer.drain()
        except asyncio.CancelledError:
            pass
        finally:
            down_writer.close()
            await down_writer.wait_closed()
            await asyncio.sleep(0)

    async def _upstream():
        try:
            while True:
                data = await down_reader.read(4096)
                if not data:
                    break
                up_writer.write(data)
                await up_writer.drain()
        except asyncio.CancelledError:
            pass
        finally:
            up_writer.close()
            await up_writer.wait_closed()
            await asyncio.sleep(0)

    loop = current_loop()
    downstream_task = loop.create_task(_downstream())
    upstream_task = loop.create_task(_upstream())
    tasks = [upstream_task, downstream_task]
    # Since we cannot determine which side (the server or client) disconnects first,
    # await until any task that completes first.
    # For example, when proxying the docker domain socket, the proxy connections for one-shot
    # docker commands are usually disconnected by the client first, but the connections for
    # long-running streaming commands are disconnected by the server first when the server-side
    # processing finishes.
    try:
        task_results: Tuple[Set[Future], Set[Future]] = \
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        done, pending = task_results
    except asyncio.CancelledError:
        pass
    finally:
        # And then cancel all remaining tasks.
        for t in pending:
            t.cancel()
            await t
