import abc
from typing import Iterable, Tuple

from .protos import raft_pb2
from .types import CommandResponse, PeerId


class AbstractRaftProtocol(abc.ABC):
    @abc.abstractmethod
    async def on_append_entries(
        self,
        *,
        term: int,
        leader_id: PeerId,
        prev_log_index: int,
        prev_log_term: int,
        entries: Iterable[raft_pb2.Log],  # type: ignore
        leader_commit: int,
    ) -> Tuple[int, bool]:
        """Receiver implementation:
        1. Reply false if term < currentTerm
        2. Reply false if log doesn't contain an entry at prevLogIndex whose term matches prevLogTerm
        3. If an existing entry conflicts with a new one (same index but different terms),
           delete the existing entry and all that follow it
        4. Append any new entries not already in the log
        5. If leaderCommit > commitIndex, set commitIndex = min(leaderCommit, index of last new entry)

        Arguments
        ---------
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
        :param int term: currentTerm, for leader to update itself
        :param bool success: true if follower contained entry matching prevLogIndex and prevLogTerm
        -------
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def on_request_vote(
        self,
        *,
        term: int,
        candidate_id: PeerId,
        last_log_index: int,
        last_log_term: int,
    ) -> Tuple[int, bool]:
        """Receiver implementation:
        1. Reply false if term < currentTerm
        2. If votedFor is null or candidateId, and candidate's log is
           at lease as up-to-date as receiver's log, grant vote

        Arguments
        ---------
        :param int term: candidate's term
        :param ai.backend.common.distributed.raft.types.PeerId candidate_id: candidate requesting vote
        :param int last_log_index: index of candidate's last log entry
        :param int last_log_term: term of candidate's last log entry
        ---------

        Returns
        -------
        :param int term: currentTerm, for candidate to update itself
        :param bool vote_granted: true means candidate received vote
        -------
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def on_install_snapshot(
        self,
        *,
        term: int,
        leader_id: PeerId,
        last_included_index: int,
        last_included_term: int,
        offset: int,
        data: bytes,
        done: bool,
    ) -> int:
        """Receiver implementation:
        1. Reply immediately if term < currentTerm
        2. Create new snapshot file if first chunk (offset is 0)
        3. Write data into snapshot file at given offset
        4. Reply and wait for more data chunks if done is false
        5. Save snapshot file, discard any existing or partial snapshot with a smaller index
        6. If existing log entry has same index and term as snapshot's last included entry,
           retain log entries following it and reply
        7. Discard the entire log
        8. Reset state machine using snapshot contents (and load snapshot's cluster configuration)

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


class AbstractRaftServiceProtocol(abc.ABC):
    @abc.abstractmethod
    async def on_command(
        self,
        *,
        id: str,
        command: str,
    ) -> CommandResponse:
        raise NotImplementedError()
