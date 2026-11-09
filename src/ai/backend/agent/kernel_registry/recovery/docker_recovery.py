from __future__ import annotations

import logging

from ai.backend.logging.structured import StructuredLogger

from .base_recovery import BaseKernelRegistryRecovery

log = StructuredLogger(logging.getLogger(__spec__.name))


class DockerKernelRegistryRecovery(BaseKernelRegistryRecovery):
    pass
