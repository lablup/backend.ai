"""Row → Data adapter for AppConfigFragment."""

from __future__ import annotations

from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow


class AppConfigFragmentAdapter:
    """Convert ORM `AppConfigFragmentRow` instances into the
    framework-free `AppConfigFragmentData` value type."""

    @staticmethod
    def to_data(row: AppConfigFragmentRow) -> AppConfigFragmentData:
        return AppConfigFragmentData(
            id=row.id,
            scope_type=row.scope_type,
            scope_id=row.scope_id,
            name=row.name,
            extra_config=dict(row.extra_config) if row.extra_config is not None else None,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
