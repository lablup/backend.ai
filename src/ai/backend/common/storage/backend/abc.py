from __future__ import annotations

from abc import ABCMeta, abstractmethod

from ai.backend.common.data.entity.storage_backend import StorageBackendID


class AbstractStorageBackendStatusCheck[TResult](metaclass=ABCMeta):
    """
    The status check of one storage appliance, and nothing else.

    It is not an abstraction of the appliance: it answers only whether the appliance is
    reachable from this service. Everything else about a backend lives elsewhere.
    """

    @property
    @abstractmethod
    def backend_id(self) -> StorageBackendID:
        """The operator-assigned id every service declaring this appliance writes down."""
        raise NotImplementedError

    @abstractmethod
    async def check_status(self) -> TResult:
        """
        Answers whether this appliance is reachable from this service.

        Separate from a volume's check because the two fail independently: an appliance
        can answer its management API while the storage has gone away on one service.
        """
        raise NotImplementedError
