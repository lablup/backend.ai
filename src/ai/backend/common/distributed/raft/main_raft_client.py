import argparse
import asyncio
import random
import uuid
from typing import Optional, Tuple

import grpc

from ai.backend.common.distributed.raft.protos import raft_pb2, raft_pb2_grpc


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "peers",
        type=str,
        nargs="+",
        help="List of raft peer's address. (e.g. 127.0.0.1:50051)",
    )
    return parser.parse_args()


async def send_request(peer: str, id: str, command: str) -> Tuple[bool, Optional[str]]:
    async with grpc.aio.insecure_channel(peer) as channel:
        stub = raft_pb2_grpc.CommandServiceStub(channel)
        request = raft_pb2.CommandRequest(id=id, command=command)
        try:
            response = await stub.Command(request)
            print(f"({peer}) response(success={response.success}, redirect={response.redirect})")
            return response.success, response.redirect
        except grpc.aio.AioRpcError as e:
            raise e


async def main():
    args = parse_args()
    peer = random.choice(args.peers)  # "[::]:50051"

    while True:
        while command := input("(redis) > "):
            success = False
            request_id = str(uuid.uuid4())
            while not success:
                try:
                    success, redirect = await send_request(peer, id=request_id, command=command)
                    if redirect:
                        peer = redirect
                        print(f"Redirect to: {redirect}")
                except grpc.aio.AioRpcError:
                    # print(f"grpc.aio.AioRpcError: {e}")
                    peer = random.choice([cand for cand in args.peers if cand != peer])
                    print(f"Choice a new peer: {peer}")


if __name__ == "__main__":
    asyncio.run(main())
