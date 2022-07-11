import abc
import asyncio
from typing import Iterable, Optional

import grpc

from .protos import raft_pb2, raft_pb2_grpc
from .types import PeerId


class AbstractRaftClient(abc.ABC):
    @abc.abstractmethod
    async def append_entries(
        self,
        *,
        address: str,
        term: int,
        leader_id: PeerId,
        entries: Iterable[raft_pb2.Log],    # type: ignore
    ) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    async def request_vote(
        self,
        *,
        address: str,
        term: int,
        candidate_id: PeerId,
        last_log_index: int,
        last_log_term: int,
    ) -> bool:
        raise NotImplementedError()


class GrpcRaftClient(AbstractRaftClient):
    """
    A grpc-based implementation of `AbstractRaftClient`.
    """
    def __init__(self, credentials: Optional[grpc.ChannelCredentials] = None):
        self._credentials: Optional[grpc.ChannelCredentials] = credentials

    async def append_entries(
        self,
        *,
        address: str,
        term: int,
        leader_id: PeerId,
        entries: Iterable[raft_pb2.Log],    # type: ignore
        timeout: float = 5.0,
    ) -> bool:
        try:
            success = await asyncio.wait_for(
                self._append_entries(address, term, leader_id, entries),
                timeout=timeout,
            )
            return success
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        return False

    async def _append_entries(
        self,
        address: str,
        term: int,
        leader_id: PeerId,
        entries: Iterable[raft_pb2.Log],    # type: ignore
    ) -> bool:
        if credentials := self._credentials:
            channel = grpc.aio.secure_channel(address, credentials)
        else:
            channel = grpc.aio.insecure_channel(address)

        stub = raft_pb2_grpc.RaftServiceStub(channel)
        request = raft_pb2.AppendEntriesRequest(term=term, leader_id=leader_id, entries=entries)
        try:
            response = await stub.AppendEntries(request)
            return response.success
        except grpc.aio.AioRpcError:
            return False
        finally:
            await channel.close()

    async def request_vote(
        self,
        *,
        address: str,
        term: int,
        candidate_id: PeerId,
        last_log_index: int,
        last_log_term: int,
        timeout: float = 5.0,
    ) -> bool:
        try:
            vote_granted = await asyncio.wait_for(
                self._request_vote(address, term, candidate_id, last_log_index, last_log_term),
                timeout=timeout,
            )
            return vote_granted
        except asyncio.TimeoutError:
            pass
        return False

    async def _request_vote(
        self,
        address: str,
        term: int,
        candidate_id: PeerId,
        last_log_index: int,
        last_log_term: int,
    ) -> bool:
        if credentials := self._credentials:
            channel = grpc.aio.secure_channel(address, credentials)
        else:
            channel = grpc.aio.insecure_channel(address)

        stub = raft_pb2_grpc.RaftServiceStub(channel)
        request = raft_pb2.RequestVoteRequest(
            term=term, candidate_id=candidate_id,
            last_log_index=last_log_index, last_log_term=last_log_term,
        )
        try:
            response = await stub.RequestVote(request)
            return response.vote_granted
        except grpc.aio.AioRpcError:
            return False
        finally:
            await channel.close()
