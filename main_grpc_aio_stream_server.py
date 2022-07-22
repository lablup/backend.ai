import asyncio
from typing import Optional

import grpc

from ai.backend.common.distributed.raft.protos import raft_pb2, raft_pb2_grpc


class RaftServiceServicer(raft_pb2_grpc.RaftServiceServicer):
    def __init__(self, credentials: Optional[grpc.ServerCredentials] = None):
        self._credentials: Optional[grpc.ServerCredentials] = credentials

    async def AppendEntries(
        self,
        request: raft_pb2.AppendEntriesRequest,
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.AppendEntriesResponse:
        return raft_pb2.AppendEntriesResponse()

    async def RequestVote(
        self,
        request: raft_pb2.RequestVoteRequest,
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.RequestVoteResponse:
        return raft_pb2.RequestVoteResponse()

    async def InstallSnapshot(
        self,
        request_iterator: grpc._cython.cygrpc._MessageReceiver,
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.InstallSnapshotResponse:
        print(f"InstallSnapshot(request_iterator: {type(request_iterator)})")
        async for request in request_iterator:
            print(f"InstallSnapshot(request: {type(request)})")
            print(f"InstallSnapshot(term={request.term}, leader={request.leader_id}, data={request.data}, done={request.done})")
        return raft_pb2.InstallSnapshotResponse(term=1)


async def main():
    server = grpc.aio.server()
    raft_pb2_grpc.add_RaftServiceServicer_to_server(RaftServiceServicer(), server)
    server.add_insecure_port("[::]:50051")

    async def server_graceful_shutdown():
        await server.stop(5)

    try:
        await server.start()
        await server.wait_for_termination()
    finally:
        await asyncio.gather(server_graceful_shutdown())


if __name__ == "__main__":
    asyncio.run(main())
