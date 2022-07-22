import argparse
import asyncio
from contextlib import suppress
from typing import Coroutine, List

from ai.backend.common.distributed.raft import RaftConsensusModule
from ai.backend.common.distributed.raft.client import GrpcRaftClient
from ai.backend.common.distributed.raft.server import GrpcRaftServer

_cleanup_coroutines: List[Coroutine] = []


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", "-p", type=int, default=50051)
    parser.add_argument(
        "peers",
        type=str,
        nargs="+",
        help="List of raft peer's address. (e.g. 127.0.0.1:50051)",
    )
    return parser.parse_args()


async def _main():
    args = parse_args()

    server = GrpcRaftServer()
    client = GrpcRaftClient()
    raft = await RaftConsensusModule.new(
        peers=args.peers, server=server, client=client, id=str(args.port)
    )

    done, pending = await asyncio.wait(
        {
            asyncio.create_task(
                server.run(cleanup_coroutines=_cleanup_coroutines, port=args.port),
            ),
            asyncio.create_task(raft.main()),
        },
        return_when=asyncio.FIRST_EXCEPTION,
    )
    for task in pending:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


async def main():
    try:
        await _main()
    finally:
        await asyncio.gather(*_cleanup_coroutines)


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
