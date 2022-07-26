import abc
from typing import Coroutine, Iterable, List, Optional, Union

import grpc

from .protocol import AbstractRaftProtocol, AbstractRaftServiceProtocol
from .protos import raft_pb2, raft_pb2_grpc


class AbstractRaftServer(abc.ABC):
    @abc.abstractmethod
    def bind(self, protocol: AbstractRaftProtocol):
        raise NotImplementedError()


class GrpcRaftServer(
    AbstractRaftServer, raft_pb2_grpc.RaftServiceServicer, raft_pb2_grpc.CommandServiceServicer
):
    """
    A grpc-based implementation of `AbstractRaftServer`.
    """

    def __init__(self, credentials: Optional[grpc.ServerCredentials] = None):
        self._raft_protocol: Optional[AbstractRaftProtocol] = None
        self._raft_service_protocol: Optional[AbstractRaftServiceProtocol] = None
        self._credentials: Optional[grpc.ServerCredentials] = credentials

    def bind(
        self,
        raft_protocol: AbstractRaftProtocol,
        raft_service_protocol: AbstractRaftServiceProtocol,
    ):
        self._raft_protocol = raft_protocol
        self._raft_service_protocol = raft_service_protocol

    async def run(self, cleanup_coroutines: List[Coroutine], host: str = "[::]", port: int = 50051):
        server = grpc.aio.server()
        raft_pb2_grpc.add_RaftServiceServicer_to_server(self, server)
        raft_pb2_grpc.add_CommandServiceServicer_to_server(self, server)

        if credentials := self._credentials:
            server.add_secure_port(f"{host}:{port}", credentials)
        else:
            server.add_insecure_port(f"{host}:{port}")

        async def server_graceful_shutdown():
            await server.stop(5)

        cleanup_coroutines.append(server_graceful_shutdown())

        await server.start()
        await server.wait_for_termination()

    """
    raft_pb2_grpc.RaftServiceServicer
    """

    async def AppendEntries(
        self,
        request: raft_pb2.AppendEntriesRequest,
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.AppendEntriesResponse:
        if (protocol := self._raft_protocol) is None:
            return raft_pb2.AppendEntriesResponse(term=request.term, success=False)
        term, success = await protocol.on_append_entries(
            term=request.term,
            leader_id=request.leader_id,
            prev_log_index=request.prev_log_index,
            prev_log_term=request.prev_log_term,
            entries=request.entries,
            leader_commit=request.leader_commit,
        )
        return raft_pb2.AppendEntriesResponse(term=term, success=success)

    async def RequestVote(
        self,
        request: raft_pb2.RequestVoteRequest,
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.RequestVoteResponse:
        if (protocol := self._raft_protocol) is None:
            return raft_pb2.RequestVoteResponse(term=request.term, vote_granted=False)
        term, vote_granted = await protocol.on_request_vote(
            term=request.term,
            candidate_id=request.candidate_id,
            last_log_index=request.last_log_index,
            last_log_term=request.last_log_term,
        )
        return raft_pb2.RequestVoteResponse(term=term, vote_granted=vote_granted)

    async def InstallSnapshot(
        self,
        request_iterator: Union[
            Iterable[raft_pb2.InstallSnapshotRequest], grpc._cython.cygrpc._MessageReceiver
        ],
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.InstallSnapshotResponse:
        pass

    """
    raft_pb2_grpc.CommandServiceServicer
    """

    async def Command(
        self,
        request: raft_pb2.CommandRequest,
        context: grpc.aio.ServicerContext,
    ) -> raft_pb2.CommandResponse:
        print(
            f"[ai.backend.common.distributed.raft] Command(id={request.id}, command={request.command})"
        )
        if (protocol := self._raft_service_protocol) is None:
            return raft_pb2.CommandResponse(success=False)
        response = await protocol.on_command(id=request.id, command=request.command)
        return raft_pb2.CommandResponse(success=response.success, redirect=response.redirect)
