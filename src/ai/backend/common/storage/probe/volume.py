from __future__ import annotations

import importlib
import pkgutil
from abc import abstractmethod
from typing import Any, ClassVar, Self, override

import ai.backend.common.storage.volume as volume_package
from ai.backend.common.configs.volume.base import VolumeConfig
from ai.backend.common.data.entity.storage_volume import StorageVolumeID
from ai.backend.common.data.storage.types import StorageBackendType, StorageStatusResult
from ai.backend.common.storage.exceptions import VolumeTypeAlreadyDeclaredError
from ai.backend.common.storage.probe.check import AbstractStatusCheck


class AbstractVolumeStatusCheck[TConfig: VolumeConfig, TResult: StorageStatusResult](
    AbstractStatusCheck[StorageVolumeID, TResult]
):
    """
    A volume's status check, built from the volume's own declaration.

    A subclass that answers ``volume_type()`` is declared for that type when its module
    is imported; ``declared()`` finds it by type. Two subclasses may not claim one type.
    """

    _declared: ClassVar[dict[StorageBackendType, type[AbstractVolumeStatusCheck[Any, Any]]]] = {}

    @override
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        try:
            volume_type = cls.volume_type()
        except NotImplementedError:
            return
        registered = AbstractVolumeStatusCheck._declared.get(volume_type)
        if registered is not None:
            raise VolumeTypeAlreadyDeclaredError(
                f"{volume_type!r} is claimed by both {registered.__name__} and {cls.__name__}"
            )
        AbstractVolumeStatusCheck._declared[volume_type] = cls

    @classmethod
    @abstractmethod
    def volume_type(cls) -> StorageBackendType:
        """The volume type this check observes."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def config_type(cls) -> type[TConfig]:
        """The schema a declaration of this volume type is validated against."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def create(cls, volume_id: StorageVolumeID, config: TConfig) -> Self:
        raise NotImplementedError

    @classmethod
    def build(cls, volume_id: StorageVolumeID, declared: VolumeConfig) -> Self:
        """Validates a declaration against this type's schema and creates the check."""
        config = cls.config_type().model_validate(declared.model_dump(by_alias=True))
        return cls.create(volume_id, config)

    @classmethod
    def declared(
        cls, volume_type: StorageBackendType
    ) -> type[AbstractVolumeStatusCheck[Any, Any]] | None:
        """The check declared for a volume type, None when no module declares one.

        Every module of the volume package is imported first, so a check is found
        whether or not the caller imported its module.
        """
        for module in pkgutil.iter_modules(volume_package.__path__):
            importlib.import_module(f"{volume_package.__name__}.{module.name}")
        return AbstractVolumeStatusCheck._declared.get(volume_type)
