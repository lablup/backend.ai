from __future__ import annotations

from abc import ABCMeta, abstractmethod

from ai.backend.common.data.storage.types import StorageAnomaly


class AbstractStatusAnomalyDetector[TResult](metaclass=ABCMeta):
    """Detects an anomaly in a check's result, compared with the result before it."""

    @abstractmethod
    def detect(self, latest: TResult | None, current: TResult) -> StorageAnomaly:
        """Whether ``current`` shows an anomaly, compared with the ``latest`` result
        before it, None when there is none."""
        raise NotImplementedError
