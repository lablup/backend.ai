from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.manager_admin import ManagerAdminRepository
from ai.backend.manager.services.manager_admin.actions.get_announcement import GetAnnouncementAction
from ai.backend.manager.services.manager_admin.actions.update_announcement import (
    UpdateAnnouncementAction,
)
from ai.backend.manager.services.manager_admin.service import ManagerAdminService

# The legacy single key and the subpaths that supersede it.
LEGACY_KEY = "manager/announcement"
MESSAGE_KEY = "manager/announcement/message"
ENABLED_KEY = "manager/announcement/enabled"


class TestManagerAdminService:
    @pytest.fixture
    def etcd_store(self) -> dict[str, str]:
        """The etcd contents backing ``mock_etcd``; starts out empty."""
        return {}

    @pytest.fixture
    def mock_etcd(self, etcd_store: dict[str, str]) -> AsyncMock:
        """An ``AsyncEtcd`` double backed by ``etcd_store``.

        It mirrors the parts of etcd's flat keyspace this service relies on: a
        key may hold a value while also serving as the path prefix of other
        keys, and prefix operations match by raw string prefix (there is no
        trailing separator), so the legacy key is swept by a replacement rooted
        at the same path.
        """

        def _get(key: str, **kwargs: Any) -> str | None:
            return etcd_store.get(key)

        def _atomic_replace_prefixes(
            replacements: Mapping[str, Mapping[str, str]], **kwargs: Any
        ) -> None:
            for prefix, contents in replacements.items():
                new_pairs = {f"{prefix}/{k}": v for k, v in contents.items()}
                for key in list(etcd_store):
                    if key.startswith(prefix) and key not in new_pairs:
                        del etcd_store[key]
                etcd_store.update(new_pairs)

        etcd = AsyncMock(spec=AsyncEtcd)
        etcd.get.side_effect = _get
        etcd.atomic_replace_prefixes.side_effect = _atomic_replace_prefixes
        return etcd

    @pytest.fixture
    def service(self, mock_etcd: AsyncMock) -> ManagerAdminService:
        return ManagerAdminService(
            repository=AsyncMock(spec=ManagerAdminRepository),
            config_provider=MagicMock(spec=ManagerConfigProvider),
            etcd=mock_etcd,
            db=MagicMock(spec=ExtendedAsyncSAEngine),
            valkey_stat=AsyncMock(spec=ValkeyStatClient),
        )


class TestGetAnnouncement(TestManagerAdminService):
    async def test_no_keys_at_all_reads_as_no_announcement(
        self,
        service: ManagerAdminService,
    ) -> None:
        result = await service.get_announcement(GetAnnouncementAction())

        assert result.enabled is False
        assert result.message == ""

    async def test_split_keys_are_read_from_their_own_subpaths(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        etcd_store.update({MESSAGE_KEY: "Maintenance at 10 PM", ENABLED_KEY: "true"})

        result = await service.get_announcement(GetAnnouncementAction())

        assert result.enabled is True
        assert result.message == "Maintenance at 10 PM"

    async def test_disabled_flag_retains_the_stored_message(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        etcd_store.update({MESSAGE_KEY: "Maintenance at 10 PM", ENABLED_KEY: "false"})

        result = await service.get_announcement(GetAnnouncementAction())

        assert result.enabled is False
        assert result.message == "Maintenance at 10 PM"

    async def test_legacy_key_alone_reads_as_enabled(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        etcd_store[LEGACY_KEY] = "Legacy announcement"

        result = await service.get_announcement(GetAnnouncementAction())

        assert result.enabled is True
        assert result.message == "Legacy announcement"

    async def test_missing_message_key_falls_back_to_the_legacy_key(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        etcd_store.update({ENABLED_KEY: "false", LEGACY_KEY: "Legacy announcement"})

        result = await service.get_announcement(GetAnnouncementAction())

        assert result.enabled is False
        assert result.message == "Legacy announcement"

    async def test_missing_enabled_key_falls_back_to_the_legacy_key(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        etcd_store.update({MESSAGE_KEY: "Maintenance at 10 PM", LEGACY_KEY: "Legacy announcement"})

        result = await service.get_announcement(GetAnnouncementAction())

        assert result.enabled is True
        assert result.message == "Maintenance at 10 PM"

    async def test_cleared_message_reads_as_empty(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        etcd_store.update({MESSAGE_KEY: "", ENABLED_KEY: "false"})

        result = await service.get_announcement(GetAnnouncementAction())

        assert result.enabled is False
        assert result.message == ""


class TestUpdateAnnouncement(TestManagerAdminService):
    @pytest.mark.parametrize("message", [None, ""])
    async def test_enabling_without_a_message_is_rejected(
        self,
        service: ManagerAdminService,
        message: str | None,
    ) -> None:
        with pytest.raises(InvalidAPIParameters):
            await service.update_announcement(
                UpdateAnnouncementAction(enabled=True, message=message)
            )

    async def test_enabling_writes_both_subpaths(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        await service.update_announcement(
            UpdateAnnouncementAction(enabled=True, message="Maintenance at 10 PM")
        )

        assert etcd_store == {MESSAGE_KEY: "Maintenance at 10 PM", ENABLED_KEY: "true"}

    async def test_disabling_without_a_message_retains_the_stored_one(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        etcd_store.update({MESSAGE_KEY: "Maintenance at 10 PM", ENABLED_KEY: "true"})

        await service.update_announcement(UpdateAnnouncementAction(enabled=False, message=None))

        assert etcd_store == {MESSAGE_KEY: "Maintenance at 10 PM", ENABLED_KEY: "false"}

    async def test_disabling_with_an_explicit_empty_message_clears_it(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        etcd_store.update({MESSAGE_KEY: "Maintenance at 10 PM", ENABLED_KEY: "true"})

        await service.update_announcement(UpdateAnnouncementAction(enabled=False, message=""))

        assert etcd_store == {MESSAGE_KEY: "", ENABLED_KEY: "false"}

    async def test_first_write_migrates_the_legacy_key_and_drops_it(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        etcd_store[LEGACY_KEY] = "Legacy announcement"

        await service.update_announcement(UpdateAnnouncementAction(enabled=False, message=None))

        assert etcd_store == {MESSAGE_KEY: "Legacy announcement", ENABLED_KEY: "false"}

    async def test_enabling_still_requires_a_message_even_when_one_is_retained(
        self,
        service: ManagerAdminService,
        etcd_store: dict[str, str],
    ) -> None:
        """Re-enabling has to resend the message; the retained one is not reused."""
        etcd_store.update({MESSAGE_KEY: "Maintenance at 10 PM", ENABLED_KEY: "false"})

        with pytest.raises(InvalidAPIParameters):
            await service.update_announcement(UpdateAnnouncementAction(enabled=True, message=None))
