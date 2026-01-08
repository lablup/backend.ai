"""Database source for app_config repository operations."""

from __future__ import annotations

from typing import Any, Optional

import sqlalchemy as sa

from ai.backend.manager.data.app_config.types import (
    AppConfigData,
    MergedAppConfig,
)
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.app_config import AppConfigRow, AppConfigScopeType
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.app_config.updaters import AppConfigUpdaterSpec
from ai.backend.manager.repositories.base.creator import Creator, execute_creator


class AppConfigDBSource:
    """
    Database source for app config operations.
    Handles all database operations for app configurations.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    async def get_config(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
    ) -> Optional[AppConfigData]:
        """Get app configuration for a specific scope."""
        async with self._db.begin_readonly_session() as db_sess:
            result = await db_sess.execute(
                sa.select(AppConfigRow).where(
                    sa.and_(
                        AppConfigRow.scope_type == scope_type,
                        AppConfigRow.scope_id == scope_id,
                    )
                )
            )
            row = result.scalar_one_or_none()
            return row.to_data() if row else None

    async def get_merged_config(
        self,
        user_id: str,
    ) -> MergedAppConfig:
        """
        Get merged configuration with override logic.
        Priority: user > domain

        Fetches user's domain information internally to query domain-level config.

        Returns:
            MergedAppConfig containing domain_name, user_id, and merged_config
        """
        async with self._db.begin_readonly_session() as db_sess:
            # Fetch user's domain name
            user_result = await db_sess.execute(
                sa.select(UserRow.domain_name).where(UserRow.uuid == user_id)
            )
            user_row = user_result.one_or_none()
            if not user_row:
                raise UserNotFound(f"User {user_id} not found")

            domain_name = user_row.domain_name
            result = await db_sess.execute(
                sa.select(AppConfigRow)
                .where(
                    sa.or_(
                        sa.and_(
                            AppConfigRow.scope_type == AppConfigScopeType.DOMAIN,
                            AppConfigRow.scope_id == domain_name,
                        ),
                        sa.and_(
                            AppConfigRow.scope_type == AppConfigScopeType.USER,
                            AppConfigRow.scope_id == user_id,
                        ),
                    )
                )
                .order_by(
                    sa.case(
                        (AppConfigRow.scope_type == AppConfigScopeType.DOMAIN, 1),
                        (AppConfigRow.scope_type == AppConfigScopeType.USER, 2),
                        else_=0,
                    )
                )
            )
            rows = result.scalars().all()

            # Merge configurations with override logic (domain first, then user)
            merged_config: dict[str, Any] = {}
            for row in rows:
                merged_config.update(row.extra_config)

            return MergedAppConfig(
                domain_name=domain_name,
                user_id=user_id,
                merged_config=merged_config,
            )

    async def create_config(self, creator: Creator[AppConfigRow]) -> AppConfigData:
        """Create a new app configuration."""
        async with self._db.begin_session() as db_sess:
            result = await execute_creator(db_sess, creator)
            return result.row.to_data()

    async def upsert_config(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
        spec: AppConfigUpdaterSpec,
    ) -> AppConfigData:
        """
        Create or update app configuration.
        If exists, update; otherwise, create new.
        """
        async with self._db.begin_session() as db_sess:
            fields_to_update = spec.build_values()
            if not fields_to_update:
                # No fields to update, just fetch existing
                result = await db_sess.execute(
                    sa.select(AppConfigRow).where(
                        sa.and_(
                            AppConfigRow.scope_type == scope_type,
                            AppConfigRow.scope_id == scope_id,
                        )
                    )
                )
                row = result.scalar_one_or_none()
                if row:
                    return row.to_data()

                # Create new with empty config
                config_row = AppConfigRow(
                    scope_type=scope_type,
                    scope_id=scope_id,
                    extra_config={},
                )
                db_sess.add(config_row)
                await db_sess.flush()
                await db_sess.refresh(config_row)
                return config_row.to_data()

            # Try to update first
            result = await db_sess.execute(
                sa.update(AppConfigRow)
                .where(
                    sa.and_(
                        AppConfigRow.scope_type == scope_type,
                        AppConfigRow.scope_id == scope_id,
                    )
                )
                .values(**fields_to_update)
            )

            if result.rowcount > 0:
                # Fetch updated row
                fetch_result = await db_sess.execute(
                    sa.select(AppConfigRow).where(
                        sa.and_(
                            AppConfigRow.scope_type == scope_type,
                            AppConfigRow.scope_id == scope_id,
                        )
                    )
                )
                row = fetch_result.scalar_one()
                return row.to_data()

            # If not exists, create new with the spec's values
            extra_config = fields_to_update.get("extra_config", {})
            config_row = AppConfigRow(
                scope_type=scope_type,
                scope_id=scope_id,
                extra_config=extra_config,
            )
            db_sess.add(config_row)
            await db_sess.flush()
            await db_sess.refresh(config_row)
            return config_row.to_data()

    async def delete_config(
        self,
        scope_type: AppConfigScopeType,
        scope_id: str,
    ) -> bool:
        """Delete an app configuration. Returns True if deleted, False if not found."""
        async with self._db.begin_session() as db_sess:
            result = await db_sess.execute(
                sa.delete(AppConfigRow).where(
                    sa.and_(
                        AppConfigRow.scope_type == scope_type,
                        AppConfigRow.scope_id == scope_id,
                    )
                )
            )
            return result.rowcount > 0
