import asyncio
import enum
import inspect
import logging
import math
import os
import random
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Final, Iterable, List, Optional, Tuple

from ...types import aobject
from .client import AbstractRaftClient
from .protocol import AbstractRaftProtocol
from .protos import raft_pb2
from .server import AbstractRaftServer
from .storage import AbstractLogStorage, RedisLogStorage
from .types import PeerId

logging.basicConfig(level=logging.INFO)

__all__ = ('RaftConsensusModule', 'RaftState')


def randrangef(start: float, stop: float) -> float:
    return random.random() * (stop - start) + start


class RaftState(enum.Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2


class RaftConsensusModule(aobject, AbstractRaftProtocol):
    def __init__(
        self,
        peers: Iterable[PeerId],
        server: AbstractRaftServer,
        client: AbstractRaftClient,
        *,
        on_state_changed: Optional[Callable[[RaftState], Awaitable]] = None,
    ) -> None:
        self._id: Final[PeerId] = str(uuid.uuid4())
        self._peers: Tuple[PeerId, ...] = tuple(peers)
        self._server: Final[AbstractRaftServer] = server
        self._client: Final[AbstractRaftClient] = client
        self._on_state_changed: Optional[Callable[[RaftState], Awaitable]] = on_state_changed

        self._election_timeout: Final[float] = randrangef(0.15, 0.3)
        self._heartbeat_interval: Final[float] = 0.1
        self._leader_id: Optional[PeerId] = None

        # Persistent state on all servers
        # (Updated on stable storage before responding to RPCs)
        self._current_term: int = 0
        self._voted_for: Optional[PeerId] = None

        # Volatile state on all servers
        self._commit_index: int = 0
        self._last_applied: int = 0

        # Volatile state on leaders
        # (Reinitialized after election)
        self._next_index: List[int] = []
        self._match_index: List[int] = []

        self._server.bind(self)

    async def __ainit__(self) -> None:
        await self._execute_transition(RaftState.FOLLOWER)
        self._log: AbstractLogStorage[raft_pb2.Log] = await RedisLogStorage[raft_pb2.Log].new()    # type: ignore

    async def _execute_transition(self, next_state: RaftState) -> None:
        self._state = next_state
        if callback := self._on_state_changed:
            if inspect.iscoroutinefunction(callback):
                await callback(next_state)
            elif inspect.isfunction(callback):
                callback(next_state)

    """
    async def _append_random_entry_coro(self):
        while True:
            await asyncio.sleep(3.0)
            command = str(uuid.uuid4())
            entry = raft_pb2.Log(index=await self._log.size(), term=self.current_term, command=command)
            await self._log.append_entries((entry,))
            while not await self.replicate_logs(entries=(entry,)):
                await asyncio.sleep(0.1)
    """

    async def main(self) -> None:
        # _append_random_entry_task: Optional[asyncio.Task] = None
        while True:
            logging.info(f'[{datetime.now().isoformat()}] pid={os.getpid()} state={self._state}')
            """
            if task := _append_random_entry_task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            """
            match self._state:
                case RaftState.FOLLOWER:
                    await self.reset_timeout()
                    await self._wait_for_election_timeout()
                    await self._execute_transition(RaftState.CANDIDATE)
                case RaftState.CANDIDATE:
                    """Rules for Servers
                    Candidates
                    - On conversion to candidate, start election:
                        - Increment currentTerm
                        - Vote for self
                        - Reset election timer
                        - Send RequestVote RPCs to all other servers
                    - If votes received from majority of servers: become leader
                    - If AppendEntries RPC received from new leader: convert to follower
                    - If election timeout elapses: start new election
                    """
                    self._leader_id = None
                    while self._state is RaftState.CANDIDATE:
                        await self._start_election()
                        if self._state is RaftState.LEADER:
                            break
                        await asyncio.sleep(self._election_timeout)
                case RaftState.LEADER:
                    logging.info(f'[{datetime.now().isoformat()}] pid={os.getpid()} LEADER({self.id})')
                    # _append_random_entry_task = asyncio.create_task(self._append_random_entry_coro())
                    self._leader_id = self.id
                    while self._state is RaftState.LEADER:
                        await self._publish_heartbeat()
                        await asyncio.sleep(self._heartbeat_interval)
            await asyncio.sleep(0)

    async def _publish_heartbeat(self) -> None:
        await self.replicate_logs(entries=())

    async def replicate_logs(self, entries: Tuple[raft_pb2.Log, ...]) -> bool:
        done, _ = await asyncio.wait({
            asyncio.create_task(
                self._client.append_entries(
                    address=address, term=self.current_term,
                    leader_id=self.id, entries=entries,
                ),
            )
            for address in self._peers
        }, return_when=asyncio.ALL_COMPLETED)
        if entries:
            logging.info(f'replicate_logs(entries={entries[-1].index}, total={await self._log.size()})')
        return sum([task.result() for task in done]) + 1 >= self.quorum

    """
    AbstractRaftProtocol Implementations
    - on_append_entries
    - on_request_vote
    """
    async def on_append_entries(
        self,
        *,
        term: int,
        leader_id: PeerId,
        prev_log_index: int,
        prev_log_term: int,
        entries: Iterable[raft_pb2.Log],    # type: ignore
        leader_commit: int,
    ) -> bool:
        """Receiver implementation:
        1. Reply false if term < currentTerm
        2. Reply false if log doesn't contain any entry at prevLogIndex whose term matches prevLogTerm
        3. If an existing entry conflicts with a new one (same index but different terms),
           delete the existing entry and all that follow it
        4. Append any new entries not already in the log
        5. If leaderCommit > commitIndex, set commitIndex = min(leaderCommit, index of last new entry)
        """
        if term < self.current_term:
            return False
        await self._synchronize_term(term)
        self._leader_id = leader_id
        await self._log.append_entries(entries)
        if tuple(entries):
            logging.info(f'[{datetime.now()}] pid={os.getpid()} on_append_entries(term={term}, entry={entries[-1].index}, '
                         f'total={await self._log.size()})')
        await self.reset_timeout()
        return True

    async def on_request_vote(
        self,
        *,
        term: int,
        candidate_id: PeerId,
        last_log_index: int,
        last_log_term: int,
    ) -> bool:
        """Receiver implementation:
        1. Reply false if term < currentTerm
        2. If votedFor is null or candidateId, and candidate's log is at least up-to-date as receiver's log, grant vote
        """
        current_term = self.current_term
        await self._synchronize_term(term)
        await self.reset_timeout()
        if term < current_term:
            return False
        if self.voted_for is None:
            self._voted_for = candidate_id
            return True
        elif self.voted_for == candidate_id:
            return True
        return False

    async def reset_timeout(self) -> None:
        self._elapsed_time: float = 0.0

    async def _wait_for_election_timeout(self, interval: float = 1.0 / 30):
        while self._elapsed_time < self._election_timeout:
            await asyncio.sleep(interval)
            self._elapsed_time += interval

    async def _start_election(self) -> None:
        await self._synchronize_term(self.current_term + 1)
        self._voted_for = self.id
        term = self.current_term
        logging.info(f'[{datetime.now().isoformat()}] pid={os.getpid()} start_election(term={term})')
        last_log = await self._log.get(-1)
        last_log_index = last_log.index if last_log else 0
        last_log_term = last_log.term if last_log else 0
        results = await asyncio.gather(*[
            asyncio.create_task(
                self._client.request_vote(
                    address=address, term=term, candidate_id=self.id,
                    last_log_index=last_log_index, last_log_term=last_log_term,
                ),
            )
            for address in self._peers
        ])
        if sum(results) + 1 >= self.quorum:
            await self._execute_transition(RaftState.LEADER)

    async def _synchronize_term(self, term: int) -> None:
        """Rules for Servers
        All Servers:
        - If RPC request or response contains term T > currentTerm: set currentTerm = T, convert to follower
        """
        if term > self.current_term:
            self._current_term = term
            await self._execute_transition(RaftState.FOLLOWER)
            self._voted_for = None

    @property
    def id(self) -> PeerId:
        return self._id

    @property
    def is_leader(self) -> bool:
        return self._leader_id == self.id

    @property
    def current_term(self) -> int:
        return self._current_term

    @property
    def voted_for(self) -> Optional[PeerId]:
        return self._voted_for

    @property
    def membership(self) -> int:
        return len(self._peers) + 1

    @property
    def quorum(self) -> int:
        return math.floor(self.membership / 2) + 1
