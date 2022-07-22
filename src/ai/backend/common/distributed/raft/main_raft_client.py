import argparse
import asyncio
import random
import uuid

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


async def main():
    args = parse_args()
    peer = random.choice(args.peers)  # "[::]:50051"

    while True:
        async with grpc.aio.insecure_channel(peer) as channel:
            stub = raft_pb2_grpc.CommandServiceStub(channel)

            while command := input("(redis) > "):
                # TODO: Verify Redis RESP command.
                request = raft_pb2.CommandRequest(
                    id=str(uuid.uuid4()),
                    command=command,
                )
                try:
                    response = await stub.Command(request)
                    print(f"response(success={response.success}, redirect={response.redirect})")
                    if not response.success and response.redirect:
                        peer = response.redirect
                        print(f"Redirect to {peer}")
                        break
                except grpc.aio.AioRpcError as e:
                    print(f"grpc.aio.AioRpcError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
