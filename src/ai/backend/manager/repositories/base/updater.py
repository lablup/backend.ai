"""Updater for repository update operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import sqlalchemy as sa

TTable = TypeVar("TTable", bound=sa.Table)


class UpdaterSpec(ABC, Generic[TTable]):
    """Abstract base class defining values to update.

    Implementations specify what to update by providing:
    - A table property that returns the target table
    - A build_values() method that returns column-value dict
    """

    @property
    @abstractmethod
    def table(self) -> TTable:
        """Return the target table for update.

        Returns:
            SQLAlchemy Table to update
        """
        raise NotImplementedError

    @abstractmethod
    def build_values(self) -> dict[str, Any]:
        """Build column name to value mapping for update.

        Returns:
            Dict mapping column names to values
        """
        raise NotImplementedError


@dataclass
class Updater(Generic[TTable]):
    """Bundles updater spec for update operations.

    Attributes:
        spec: UpdaterSpec implementation defining what to update.
    """

    spec: UpdaterSpec[TTable]
