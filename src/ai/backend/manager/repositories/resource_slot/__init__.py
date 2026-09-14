"""Resource Slot repository package."""

from .repositories import ResourceSlotRepositories
from .repository import ResourceSlotRepository

__all__ = (
    # Repositories
    "ResourceSlotRepositories",
    "ResourceSlotRepository",
    # Upserter specs
)
