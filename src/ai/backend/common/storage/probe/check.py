from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Hashable

from ai.backend.common.data.storage.types import StorageStatusResult


class AbstractProbeCheck[TID: Hashable](metaclass=ABCMeta):
    """
    One storage subject's status check, as the probe that runs it sees it.

    It is not an abstraction of the subject: it observes whether the subject is reachable
    from the service holding it. File operations and appliance management live elsewhere.
    """

    @abstractmethod
    def id(self) -> TID:
        """The operator-assigned id every service declaring this subject writes down."""
        raise NotImplementedError

    @abstractmethod
    async def check_status(self) -> None:
        """
        Observes the subject and records what it saw, judging none of it.

        It raises nothing: an observation that failed is recorded in the result instead.
        """
        raise NotImplementedError


class AbstractStatusCheck[TID: Hashable, TResult: StorageStatusResult](AbstractProbeCheck[TID]):
    """A probe check that keeps its last observation for whoever reports it to read."""

    @abstractmethod
    def latest(self) -> TResult | None:
        """What the last check observed, None until one has run."""
        raise NotImplementedError
