from abc import ABC, abstractmethod
from collections.abc import Iterable

from ai.backend.manager.sokovan.scheduler.types import AllocationSnapshot, SessionWorkload


class AllocationUpdater(ABC):
    """
    An abstract base class for allocation updaters.
    Subclasses should implement the `update` method to apply specific update logic.
    """

    @abstractmethod
    def update(self, workload: SessionWorkload, snapshot: AllocationSnapshot) -> None:
        raise NotImplementedError("Subclasses should implement this method.")


class AllocationApplier(ABC):
    """
    An abstract base class for allocation appliers.
    Subclasses should implement the `apply` method to apply specific allocation logic.
    """

    @abstractmethod
    def apply(self, snapshot: AllocationSnapshot) -> None:
        raise NotImplementedError("Subclasses should implement this method.")


class ResourceAllocator:
    _updaters: Iterable[AllocationUpdater]
    _applier: AllocationApplier

    def __init__(self, updaters: Iterable[AllocationUpdater], applier: AllocationApplier) -> None:
        self._updaters = updaters
        self._applier = applier

    def allocate(self, workload: SessionWorkload, snapshot: AllocationSnapshot) -> None:
        """
        Perform allocation by updating the snapshot with all updaters and then applying the final allocation.
        """
        for updater in self._updaters:
            updater.update(workload, snapshot)
        self._applier.apply(snapshot)
