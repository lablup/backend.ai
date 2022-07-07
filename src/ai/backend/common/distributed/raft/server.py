import abc
import logging
from typing import Coroutine, List, Optional

import grpc

from ..protos import raft_pb2, raft_pb2_grpc
from .protocol import RaftProtocol

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
        request: raft_pb2.AppendEntriesRequest,                                             # type: ignore
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.AppendEntriesResponse:                                                    # type: ignore
        if (protocol := self._protocol) is None:
            return raft_pb2.AppendEntriesResponse(term=request.term, success=False)         # type: ignore
        success = protocol.on_append_entries(
            term=request.term, leader_id=request.leader_id,                                 # type: ignore
            prev_log_index=request.prev_log_index, prev_log_term=request.prev_log_term,     # type: ignore
            entries=request.entries, leader_commit=request.leader_commit,                   # type: ignore
        )
        return raft_pb2.AppendEntriesResponse(term=request.term, success=success)           # type: ignore

    def RequestVote(
        self,
        request: raft_pb2.RequestVoteRequest,                                               # type: ignore
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.RequestVoteResponse:                                                      # type: ignore
        if (protocol := self._protocol) is None:
            return raft_pb2.RequestVoteResponse(term=request.term, vote_granted=False)      # type: ignore
        vote_granted = protocol.on_request_vote(
            term=request.term, candidate_id=request.candidate_id,                           # type: ignore
            last_log_index=request.last_log_index, last_log_term=request.last_log_term,     # type: ignore
        )
        return raft_pb2.RequestVoteResponse(term=request.term, vote_granted=vote_granted)   # type: ignore

    async def run(self, cleanup_coroutines: List[Coroutine], port: int = 50051):
        server = grpc.aio.server()
        raft_pb2_grpc.add_RaftServiceServicer_to_server(self, server)
        server.add_insecure_port(f'[::]:{port}')

        async def server_graceful_shutdown():
            await server.stop(5)

        cleanup_coroutines.append(server_graceful_shutdown())
        await server.start()
        await server.wait_for_termination()
