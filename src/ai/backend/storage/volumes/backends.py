from __future__ import annotations

from collections.abc import Mapping

from .abc import AbstractVolume
from .cephfs import CephFSVolume
from .ddn import EXAScalerFSVolume
from .dellemc import DellEMCOneFSVolume
from .gpfs import GPFSVolume
from .hammerspace.volume.base import BaseHammerspaceVolume
from .hammerspace.volume.extended import HammerspaceVolume
from .netapp import NetAppVolume
from .noop import NoopVolume
from .purestorage import FlashBladeVolume
from .vast import VASTVolume
from .vfs import BaseVolume
from .weka import WekaVolume
from .xfs import XfsVolume

DEFAULT_BACKENDS: Mapping[str, type[AbstractVolume]] = {
    FlashBladeVolume.name: FlashBladeVolume,
    BaseVolume.name: BaseVolume,
    XfsVolume.name: XfsVolume,
    NetAppVolume.name: NetAppVolume,
    # NOTE: Dell EMC has two different storage: PowerStore and PowerScale (OneFS).
    #       We support the latter only for now.
    DellEMCOneFSVolume.name: DellEMCOneFSVolume,
    WekaVolume.name: WekaVolume,
    GPFSVolume.name: GPFSVolume,  # IBM SpectrumScale or GPFS
    "spectrumscale": GPFSVolume,  # IBM SpectrumScale or GPFS
    CephFSVolume.name: CephFSVolume,
    VASTVolume.name: VASTVolume,
    EXAScalerFSVolume.name: EXAScalerFSVolume,
    NoopVolume.name: NoopVolume,
    HammerspaceVolume.name: HammerspaceVolume,
    BaseHammerspaceVolume.name: BaseHammerspaceVolume,
}
