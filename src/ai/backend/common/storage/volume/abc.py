from __future__ import annotations

from abc import ABCMeta, abstractmethod

from ai.backend.common.data.entity.storage_volume import StorageVolumeID


class AbstractVolumeStatusCheck[TResult](metaclass=ABCMeta):
    """
    The status check of one volume, and nothing else.

    It is not an abstraction of the volume: it answers only whether the volume is usable
    on the service holding it. File and vfolder operations live elsewhere.
    """

    @property
    @abstractmethod
    def volume_id(self) -> StorageVolumeID:
        """The operator-assigned id every service declaring this volume writes down."""
        raise NotImplementedError

    @abstractmethod
    async def check_status(self) -> TResult:
        """
        Answers whether this volume is usable right now.

        How that is decided is entirely the implementation's own: a device id
        comparison, filesystem statistics, a marker file, a vendor API call, or none.
        """
        raise NotImplementedError
