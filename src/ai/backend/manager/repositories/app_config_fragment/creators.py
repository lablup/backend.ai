"""CreatorSpec for AppConfigFragment rows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.data.app_config_fragment.types import default_rank_for_scope_type
from ai.backend.manager.errors.app_config import AppConfigFragmentConflict
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class AppConfigFragmentCreatorSpec(CreatorSpec[AppConfigFragmentRow]):
    """CreatorSpec for `app_config_fragments`.

    Maps the natural-key UNIQUE violation to a typed domain error
    (:class:`AppConfigFragmentConflict`). `rank` (merge priority) defaults
    to a per-scope_type tier when not explicitly provided.
    """

    scope_type: str
    scope_id: str
    name: str
    config: Mapping[str, Any]
    rank: int | None = None

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=AppConfigFragmentConflict(
                    extra_msg=(
                        f"Duplicate fragment for ({self.scope_type}, {self.scope_id}, {self.name})"
                    ),
                ),
            ),
        )

    @override
    def build_row(self) -> AppConfigFragmentRow:
        rank = self.rank if self.rank is not None else default_rank_for_scope_type(self.scope_type)
        return AppConfigFragmentRow(
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            name=self.name,
            rank=rank,
            config=dict(self.config),
        )
