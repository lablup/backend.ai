"""
Data types returned by ScheduleCacheSource.
These types include transformation methods to convert to common entities.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ai.backend.common.types import AccessKey
from ai.backend.manager.sokovan.scheduler.types import ConcurrencySnapshot

if TYPE_CHECKING:
    pass


@dataclass
class CacheConcurrencyData:
    """Concurrency data fetched from cache (Redis/Valkey)."""

    sessions_by_keypair: dict[AccessKey, int]
    sftp_sessions_by_keypair: dict[AccessKey, int]

    def to_concurrency_snapshot(self) -> ConcurrencySnapshot:
        """Convert to ConcurrencySnapshot entity."""
        return ConcurrencySnapshot(
            sessions_by_keypair=self.sessions_by_keypair,
            sftp_sessions_by_keypair=self.sftp_sessions_by_keypair,
        )


@dataclass
class CacheConcurrencyUpdate:
    """Concurrency updates to be applied to cache."""

    regular: dict[AccessKey, int]  # Regular session concurrency changes
    sftp: dict[AccessKey, int]  # SFTP session concurrency changes
