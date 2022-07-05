import asyncio
import enum
import logging
import math
import random
import uuid
from datetime import datetime
from typing import Callable, Final, Iterable, Optional

from .client import RaftClient
from .protocol import RaftProtocol
from .server import RaftServer

__all__ = ('RaftFiniteStateMachine', 'RaftState')


class RaftState(enum.Enum):
    FOLLOWER = 0
    CANDIDATE = 1
    LEADER = 2


def randrangef(start: float, stop: float) -> float:
    return random.random() * (stop - start) + start


class RaftFiniteStateMachine(RaftProtocol):
    def __init__(
        self,
        peers: Iterable[str],
        server: RaftServer,
        client: RaftClient,
        *,
        on_state_changed: Optional[Callable] = None,
    ):
        self._id = str(uuid.uuid4())
        self._current_term: int = 0
        self._last_voted_term: int = 0
        self._election_timeout: float = randrangef(0.15, 0.3)
        self._heartbeat_interval: Final[float] = 0.1
        self._peers = tuple(peers)
        self._server = server
        self._client = client
        self._leader_id: Optional[str] = None

        self._on_state_changed: Optional[Callable[[RaftState], None]] = on_state_changed

        self.execute_transition(RaftState.FOLLOWER)
        self._server.bind(self)

    async def main(self):
        while True:
            match self._state:
                case RaftState.FOLLOWER:
                    self.reset_timeout()
                    await self._wait_for_election_timeout()
                    self.execute_transition(RaftState.CANDIDATE)
                case RaftState.CANDIDATE:
                    self._leader_id = None
                    while self._state is RaftState.CANDIDATE:
                        await self._request_vote()
                        if self._state is RaftState.LEADER:
                            break
                        await asyncio.sleep(self._election_timeout)
                case RaftState.LEADER:
                    logging.info(f'[{datetime.now().isoformat()}] LEADER: {self.id}')
                    self._leader_id = self.id
                    while self._state is RaftState.LEADER:
                        await self._publish_heartbeat()
                        await asyncio.sleep(self._heartbeat_interval)
            await asyncio.sleep(0)

    def execute_transition(self, next_state: RaftState):
        self._state = next_state
        getattr(self._on_state_changed, '__call__', lambda _: None)(next_state)

    """
    External Transitions
    """
    def on_append_entries(
        self,
        *,
        term: int,
        leader_id: str,
        prev_log_index: int,
        prev_log_term: int,
        entries: Iterable[str],
        leader_commit: int,
    ) -> bool:
        current_term = self._synchronize_term(term)
        self._leader_id = leader_id
        logging.info(f'[{datetime.now().isoformat()}] [on_append_entries] term={term} leader={leader_id[:2]}')
        self.reset_timeout()
        if term >= current_term:
            self.execute_transition(RaftState.FOLLOWER)
        if term < current_term:
            return False
        return True

    def on_request_vote(
        self,
        *,
        term: int,
        candidate_id: str,
        last_log_index: int,
        last_log_term: int,
    ) -> bool:
        logging.info(f'[{datetime.now().isoformat()}] [on_request_vote] '
                     f'term={term} cand={candidate_id[:2]} (last={self._last_voted_term})')
        current_term = self._synchronize_term(term)
        # 1. Reply false if term < currentTerm.
        self.reset_timeout()
        if term < current_term:
            return False
        # 2. If votedFor is null or candidateId, and candidate's log is at least up-to-date as receiver's log, grant vote.
        if self._last_voted_term < term:
            self._last_voted_term = term
            return True
        return False

    def reset_timeout(self):
        self._elapsed_time: float = 0.0

    async def _wait_for_election_timeout(self, interval: float = 1.0 / 30):
        while self._elapsed_time < self._election_timeout:
            await asyncio.sleep(interval)
            self._elapsed_time += interval

    async def _request_vote(self):
        term = self._current_term = self.current_term + 1
        self.execute_transition(RaftState.CANDIDATE)
        self._last_voted_term = term
        logging.info(f'[_request_vote] term={term} last_vote={self._last_voted_term}')
        results = await asyncio.gather(*[
            asyncio.create_task(
                self._client.request_vote(
                    address=peer, term=term, candidate_id=self.id,
                    last_log_index=0, last_log_term=0,
                ),
            )
            for peer in self._peers
        ])
        if sum(results) + 1 >= self.quorum:
            self.execute_transition(RaftState.LEADER)

    async def _publish_heartbeat(self):
        await asyncio.wait({
            asyncio.create_task(
                self._client.request_append_entries(
                    address=peer, term=self._current_term,
                    leader_id=self.id, entries=(),
                    # timeout=heartbeat_interval,
                ),
            )
            for peer in self._peers
        }, return_when=asyncio.ALL_COMPLETED)

    def _synchronize_term(self, term: int) -> int:
        """
        All Servers:
        - If RPC request or response contains term T > currentTerm: set currentTerm = T, convert to follower.
        """
        current_term = self.current_term
        self._current_term = max(self.current_term, term)
        return current_term

    @property
    def id(self) -> str:
        return self._id

    @property
    def is_leader(self) -> bool:
        return self._leader_id == self._id

    @property
    def current_term(self) -> int:
        return self._current_term

    @property
    def quorum(self) -> int:
        return math.floor((len(self._peers) + 1) / 2) + 1
