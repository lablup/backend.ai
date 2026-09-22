"""Type definitions for repository layer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from ai.backend.manager.models.specs.types import IntegrityErrorCheck as IntegrityErrorCheck

if TYPE_CHECKING:
    from sqlalchemy.engine import Row

TRow = TypeVar("TRow", bound="Row[Any]")
