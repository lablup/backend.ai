"""CreatorSpec for AppConfigPolicy rows."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.errors.app_config import AppConfigPolicyConflict
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class AppConfigPolicyCreatorSpec(CreatorSpec[AppConfigPolicyRow]):
    """CreatorSpec for `app_config_policies`.

    `config_name` is UNIQUE and immutable — duplicate inserts surface as
    :class:`AppConfigPolicyConflict` via ``integrity_error_checks``.
    """

    config_name: str
    scope_sources: Sequence[str]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=AppConfigPolicyConflict(
                    extra_msg=f"Duplicate config_name: {self.config_name}",
                ),
            ),
        )

    @override
    def build_row(self) -> AppConfigPolicyRow:
        return AppConfigPolicyRow(
            config_name=self.config_name,
            scope_sources=list(self.scope_sources),
        )
