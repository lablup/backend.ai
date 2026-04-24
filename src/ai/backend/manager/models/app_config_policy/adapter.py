"""Row → Data adapter for AppConfigPolicy."""

from __future__ import annotations

from ai.backend.manager.data.app_config_policy.types import AppConfigPolicyData
from ai.backend.manager.models.app_config_policy.row import AppConfigPolicyRow


class AppConfigPolicyAdapter:
    """Convert ORM `AppConfigPolicyRow` instances into the
    framework-free `AppConfigPolicyData` value type."""

    @staticmethod
    def to_data(row: AppConfigPolicyRow) -> AppConfigPolicyData:
        return AppConfigPolicyData(
            id=row.id,
            config_name=row.config_name,
            scope_sources=list(row.scope_sources),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
