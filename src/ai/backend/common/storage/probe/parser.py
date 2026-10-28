from __future__ import annotations

from abc import ABCMeta, abstractmethod

from ai.backend.common.data.storage.types import StorageStatusResultData


class AbstractStatusDataParser[TResult](metaclass=ABCMeta):
    """Converts a check's result to the shape it is reported in, and back."""

    @abstractmethod
    def to_result_data(self, result: TResult | None) -> StorageStatusResultData:
        """The reported shape of ``result``, not checked while it is None. Raises
        :class:`InvalidStorageStatusObservation` when it is not one the check records."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, data: StorageStatusResultData) -> TResult | None:
        """The result ``data`` reports, None while no check has run. Raises
        :class:`InvalidStorageStatusObservation` when it is not one the check records."""
        raise NotImplementedError
