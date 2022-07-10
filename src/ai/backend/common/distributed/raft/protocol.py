import abc
from typing import Iterable


class AbstractRaftProtocol(abc.ABC):
    @abc.abstractmethod
    async def on_append_entries(
        self,
        *,
        term: int,
        leader_id: str,
        prev_log_index: int,
        prev_log_term: int,
        entries: Iterable[str],
        leader_commit: int,
    ) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    async def on_request_vote(
        self,
        *,
        term: int,
        candidate_id: str,
        last_log_index: int,
        last_log_term: int,
    ) -> bool:
        raise NotImplementedError()
