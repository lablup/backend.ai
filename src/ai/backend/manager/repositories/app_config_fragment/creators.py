"""CreatorSpec implementations for app config fragment repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.identifier.app_config import AppConfigScopeIdentifier
from ai.backend.manager.errors.app_config import AppConfigFragmentWriteNotAllowed
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.repositories.base import CreatorSpec, IntegrityErrorCheck


@dataclass
class AppConfigFragmentCreatorSpec(CreatorSpec[AppConfigFragmentRow]):
    """CreatorSpec for one app config fragment.

    The fragment carries no merge priority of its own — its rank is the ``rank`` of
    the allow-list entry for its ``(config_name, scope_type)``.
    """

    config_name: str
    scope_type: AppConfigScopeType
    scope_id: AppConfigScopeIdentifier
    config: dict[str, Any]

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        # The FK to app_config_allow_list is the only gate: an insert with no
        # allow-list row for (config_name, scope_type) surfaces as write-not-allowed.
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_app_config_fragments_config_name_scope_type",
                error=AppConfigFragmentWriteNotAllowed(
                    f"Writing app config {self.config_name!r} at scope "
                    f"{self.scope_type.value!r} is not allowed."
                ),
            ),
        )

    @override
    def build_row(self) -> AppConfigFragmentRow:
        return AppConfigFragmentRow(
            config_name=self.config_name,
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            config=self.config,
        )
