import asyncio
import uuid

import grpc

from ai.backend.common.distributed.raft.protos import raft_pb2, raft_pb2_grpc


async def main():
    async with grpc.aio.insecure_channel("[::]:50051") as channel:
        stub = raft_pb2_grpc.RaftServiceStub(channel)

        def request_iterator():
            number_of_chunks = 8
            for idx in range(1, number_of_chunks + 1):
                yield raft_pb2.InstallSnapshotRequest(
                    term=1,
                    leader_id="lablup",
                    last_included_index=1,
                    last_included_term=1,
                    offset=0,
                    data=str(uuid.uuid4()).encode("utf-8"),
                    done=(idx == number_of_chunks),
                )
        try:
            response = await stub.InstallSnapshot(request_iterator())
            print(f"response(term={response.term})")
        except grpc.aio.AioRpcError as e:
            print(f"grpc.aio.AioRpcError: {e}")


if __name__ == "__main__":
    asyncio.run(main())
