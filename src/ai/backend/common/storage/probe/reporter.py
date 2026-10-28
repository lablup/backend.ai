from __future__ import annotations

from abc import ABCMeta, abstractmethod
from collections.abc import Mapping
from typing import override

from ai.backend.common.data.entity.storage_volume import StorageVolumeName
from ai.backend.common.data.storage.types import StorageStatusResultData
from ai.backend.common.storage.probe.parser import AbstractStatusDataParser
from ai.backend.common.storage.probe.volume import AbstractVolumeStatusCheck


class AbstractVolumeStatusReporter(metaclass=ABCMeta):
    """Reports a volume status check's last result, without the result type, so
    reporters of different result types share one registry."""

    @abstractmethod
    def report(self) -> Mapping[StorageVolumeName, StorageStatusResultData]:
        """The check's last result by volume, in the shape it is reported in. Raises
        :class:`InvalidStorageStatusObservation` when the parser rejects it."""
        raise NotImplementedError


class VolumeStatusReporter[TResult](AbstractVolumeStatusReporter):
    """Reports a volume status check's result through the parser of its result type."""

    _check: AbstractVolumeStatusCheck[TResult]
    _data_parser: AbstractStatusDataParser[TResult]

    def __init__(
        self,
        check: AbstractVolumeStatusCheck[TResult],
        data_parser: AbstractStatusDataParser[TResult],
    ) -> None:
        self._check = check
        self._data_parser = data_parser

    @override
    def report(self) -> Mapping[StorageVolumeName, StorageStatusResultData]:
        return {self._check.id(): self._data_parser.to_result_data(self._check.latest())}
