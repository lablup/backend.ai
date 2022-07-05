import abc
from typing import Iterable


class RaftProtocol(abc.ABC):
    @abc.abstractmethod
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
        raise NotImplementedError()

    @abc.abstractmethod
    def on_request_vote(
        self,
        *,
        term: int,
        candidate_id: str,
        last_log_index: int,
        last_log_term: int,
    ) -> bool:
        raise NotImplementedError()
