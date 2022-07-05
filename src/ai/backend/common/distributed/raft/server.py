import abc
import logging
from typing import Coroutine, List, Optional

import grpc

from .protocol import RaftProtocol
from ..protos import raft_pb2, raft_pb2_grpc

logging.basicConfig(level=logging.INFO)


class RaftServer(abc.ABC):
    @abc.abstractmethod
    def bind(self, protocol: RaftProtocol):
        raise NotImplementedError()


class GrpcRaftServer(RaftServer, raft_pb2_grpc.RaftServiceServicer):
    def __init__(self):
        self._protocol: Optional[RaftProtocol] = None

    def bind(self, protocol: RaftProtocol):
        self._protocol = protocol

    def AppendEntries(
        self,
        request: raft_pb2.AppendEntriesRequest,
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.AppendEntriesResponse:
        success = self._protocol.on_append_entries(
            term=request.term, leader_id=request.leader_id,
            prev_log_index=request.prev_log_index, prev_log_term=request.prev_log_term,
            entries=request.entries, leader_commit=request.leader_commit,
        )
        return raft_pb2.AppendEntriesResponse(term=request.term, success=success)

    def RequestVote(
        self,
        request: raft_pb2.RequestVoteRequest,
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.RequestVoteResponse:
        vote_granted = self._protocol.on_request_vote(
            term=request.term, candidate_id=request.candidate_id,
            last_log_index=request.last_log_index, last_log_term=request.last_log_term,
        )
        return raft_pb2.RequestVoteResponse(term=request.term, vote_granted=vote_granted)

    @staticmethod
    async def run(servicer: raft_pb2_grpc.RaftServiceServicer, cleanup_coroutines: List[Coroutine], port: int = 50051):
        server = grpc.aio.server()
        raft_pb2_grpc.add_RaftServiceServicer_to_server(servicer, server)
        server.add_insecure_port(f'[::]:{port}')

        async def server_graceful_shutdown():
            await server.stop(5)

        cleanup_coroutines.append(server_graceful_shutdown())

        await server.start()

        await server.wait_for_termination()


if __name__ == '__main__':
    import asyncio
    asyncio.run(
        GrpcRaftServer.run(
            servicer=GrpcRaftServer(),
            cleanup_coroutines=[],
            port=50051,
        ),
    )
