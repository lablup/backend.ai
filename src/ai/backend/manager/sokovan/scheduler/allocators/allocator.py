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

    def allocate(self, workload: SessionWorkload) -> None:
        """
        Perform allocation by creating a snapshot, updating it with all updaters,
        and then applying the final allocation.
        """
        # Create allocation snapshot internally
        snapshot = AllocationSnapshot(
            session_id=workload.session_id,
            session_type=workload.session_type,
            cluster_mode=workload.cluster_mode,
            kernel_allocations=[],
        )

        # Update the snapshot with each updater
        for updater in self._updaters:
            updater.update(workload, snapshot)

        # Apply the allocation
        self._applier.apply(snapshot)
