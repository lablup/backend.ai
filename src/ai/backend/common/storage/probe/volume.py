from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sequence

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.storage.probe.check import AbstractStatusCheck
from ai.backend.common.storage.probe.parser import AbstractStatusDataParser


class AbstractVolumeStatusCheck(AbstractStatusCheck[StorageVolumeName]):
    """A volume's status check."""

    @abstractmethod
    def data_parser(self) -> AbstractStatusDataParser[TResult]:
        """The parser that reads this check's reported observations back into results."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def judge_health(cls, history: Sequence[TResult], current: TResult) -> StorageHealthStatus:
        """Whether the volume is in order, judged from its current result against the
        earlier results in ``history``, oldest first."""
        raise NotImplementedError
