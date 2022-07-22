import abc
import asyncio
from typing import Iterable, Optional, Tuple

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
        prev_log_index: int,
        prev_log_term: int,
        entries: Iterable[raft_pb2.Log],  # type: ignore
        leader_commit: int,
    ) -> Tuple[int, bool]:
        """Invoked by leader to replicate log entries; also used as heartbeat.

        Arguments
        ---------
        :param str address: follower's IP address with port (e.g. "127.0.0.1:50051")
        :param int term: leader's term
        :param ai.backend.common.distributed.raft.types.PeerId leader_id: so follower can redirect clients
        :param int prev_log_index: index of log entry immediately preceding new ones
        :param int prev_log_term: term of prevLogIndex entry
        :param Iterable[ai.backend.common.distributed.raft.protos.raft_pb2.Log] entries: log entries to store
            (empty for heartbeat; may send more than one for efficiency)
        :param int leader_commit: leader's commitIndex
        ---------

        Returns
        -------
        :param int term: follower's currentTerm, for leader to update itself
        :param bool success: true if follower contained entry matching prevLogIndex and prevLogTerm
        -------
        """
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
    ) -> Tuple[int, bool]:
        """Invoked by candidates to gather votes.

        Arguments
        ---------
        :param str address: follower's IP address with port (e.g. "127.0.0.1:50051")
        :param int term: candidate's term
        :param ai.backend.common.distributed.raft.types.PeerId candidate_id: candidate requesting vote
        :param int last_log_index: index of candidate's last log entry
        :param int last_log_term: term of candidate's last log entry
        ---------

        Returns
        -------
        :param int term: follower's currentTerm, for candidate to update itself
        :param bool vote_granted: true means candidate received vote
        -------
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def install_snapshot(
        self,
        *,
        address: str,
        term: int,
        leader_id: PeerId,
        last_included_index: int,
        last_included_term: int,
        offset: int,
        data: bytes,
        done: bool,
    ) -> int:
        """Invoked by leader to send chunks of a snapshot to a follower.
        Leaders always send chunks in order.

        Arguments
        ---------
        :param int term: leader's term
        :param ai.backend.common.distributed.raft.types.PeerId leader_id:
            so follower can redirect clients
        :param int last_included_index:
            the snapshot replaces all entries up through and including this index
        :param int last_included_term: term of lastIncludedIndex
        :param int offset: byte offset where chunk is positioned in the snapshot file
        :param bytes data: raw bytes of the snapshot chunk, starting at offset
        :param bool done: true if this is the last chunk
        ---------

        Returns
        -------
        :param int term: currentTerm, for leader to update itself
        -------
        """
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
        prev_log_index: int,
        prev_log_term: int,
        entries: Iterable[raft_pb2.Log],  # type: ignore
        leader_commit: int,
        timeout: float = 5.0,
    ) -> Tuple[int, bool]:
        try:
            term, success = await asyncio.wait_for(
                self._append_entries(
                    address, term, leader_id, prev_log_index, prev_log_term, entries, leader_commit
                ),
                timeout=timeout,
            )
            return term, success
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        return term, False

    async def _append_entries(
        self,
        address: str,
        term: int,
        leader_id: PeerId,
        prev_log_index: int,
        prev_log_term: int,
        entries: Iterable[raft_pb2.Log],  # type: ignore
        leader_commit: int,
    ) -> Tuple[int, bool]:
        channel = self.make_channel(address)
        stub = raft_pb2_grpc.RaftServiceStub(channel)
        request = raft_pb2.AppendEntriesRequest(
            term=term,
            leader_id=leader_id,
            prev_log_index=prev_log_index,
            prev_log_term=prev_log_term,
            entries=entries,
            leader_commit=leader_commit,
        )
        try:
            response = await stub.AppendEntries(request)
            return response.term, response.success
        except grpc.aio.AioRpcError:
            return term, False
        finally:
            # FIXME: contextmanager using with statement?
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
    ) -> Tuple[int, bool]:
        try:
            term, vote_granted = await asyncio.wait_for(
                self._request_vote(address, term, candidate_id, last_log_index, last_log_term),
                timeout=timeout,
            )
            return term, vote_granted
        except asyncio.TimeoutError:
            pass
        return term, False

    async def _request_vote(
        self,
        address: str,
        term: int,
        candidate_id: PeerId,
        last_log_index: int,
        last_log_term: int,
    ) -> Tuple[int, bool]:
        channel = self.make_channel(address)
        stub = raft_pb2_grpc.RaftServiceStub(channel)
        request = raft_pb2.RequestVoteRequest(
            term=term,
            candidate_id=candidate_id,
            last_log_index=last_log_index,
            last_log_term=last_log_term,
        )
        try:
            response = await stub.RequestVote(request)
            return response.term, response.vote_granted
        except grpc.aio.AioRpcError:
            return term, False
        finally:
            # FIXME: contextmanager using with statement?
            await channel.close()

    async def install_snapshot(
        self,
        *,
        address: str,
        term: int,
        leader_id: PeerId,
        last_included_index: int,
        last_included_term: int,
        offset: int,
        data: bytes,
        done: bool,
    ) -> int:
        channel = self.make_channel(address)
        stub = raft_pb2_grpc.RaftServiceStub(channel)
        request = raft_pb2.InstallSnapshotRequest(
            term=term,
            leader_id=leader_id,
            last_included_index=last_included_index,
            last_included_term=last_included_term,
            offset=offset,
            data=data,
            done=done,
        )
        try:
            response = await stub.InstallSnapshot(request)
            return response.term
        except grpc.aio.AioRpcError:
            return 0
        finally:
            # FIXME: contextmanager using with statement?
            await channel.close()

    def make_channel(self, address: str) -> grpc.aio.Channel:
        if credentials := self._credentials:
            return grpc.aio.secure_channel(address, credentials)
        return grpc.aio.insecure_channel(address)
