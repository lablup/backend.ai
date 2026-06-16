"""CreatorSpec for AppConfigFragment rows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.manager.errors.app_config import AppConfigFragmentConflict
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base.creator import DependentCreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class AppConfigFragmentCreatorSpec(DependentCreatorSpec[int, AppConfigFragmentRow]):
    """CreatorSpec for `app_config_fragments`.

    `rank` (merge priority within `name`) is assigned by the ops layer
    (next-value: ``MAX(rank) + gap`` within the `name`) at execution — the
    same pattern as DeploymentRevisionPreset; ``build_row`` receives the
    computed next rank as its dependency.

    Maps the natural-key UNIQUE violation to a typed domain error
    (:class:`AppConfigFragmentConflict`).
    """

    scope_type: str
    scope_id: str
    name: str
    config: Mapping[str, Any]

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
    def build_row(self, next_rank: int) -> AppConfigFragmentRow:
        return AppConfigFragmentRow(
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            name=self.name,
            rank=next_rank,
            config=dict(self.config),
        )
