from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Hashable

from ai.backend.common.data.storage.types import StorageStatusResult


class AbstractStatusCheck[TID: Hashable](metaclass=ABCMeta):
    """
    The status check of one storage subject, a volume or a backend appliance, and nothing else.

    It is not an abstraction of the subject: it answers only whether the subject is usable
    from the service holding it. File operations and appliance management live elsewhere.
    """

    @abstractmethod
    def get_id(self) -> TID:
        """The operator-assigned id every service declaring this subject writes down."""
        raise NotImplementedError

    @abstractmethod
    def get_latest(self) -> StorageStatusResult | None:
        """What the last check found, None until one has run."""
        raise NotImplementedError

    @abstractmethod
    def check_status(self) -> None:
        """
        Runs the check and records what it found for ``get_latest()`` to answer with.

        Called in a thread of its own, so it blocks rather than awaits, and it raises
        nothing: a failure is recorded as the result's ``error_msg``.
        """
        raise NotImplementedError
