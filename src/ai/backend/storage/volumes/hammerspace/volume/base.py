from __future__ import annotations

import logging
from typing import (
    ClassVar,
    override,
)

from ai.backend.logging import BraceStyleAdapter

from ....types import CapacityUsage
from ...abc import (
    CAP_VFOLDER,
)
from ...vfs import BaseVolume

log = BraceStyleAdapter(logging.getLogger(__name__))


class BaseHammerspaceVolume(BaseVolume):
    name: ClassVar[str] = "hammerspace-base"

    @override
    async def get_capabilities(self) -> frozenset[str]:
        return frozenset([CAP_VFOLDER])

    @override
    async def get_fs_usage(self) -> CapacityUsage:
        return CapacityUsage(
            capacity_bytes=-1,
            used_bytes=-1,
        )
