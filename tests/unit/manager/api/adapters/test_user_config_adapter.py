from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.common.dotfile import InvalidDotfilePath
from ai.backend.manager.api.adapters.user.config import UserConfigAdapter
from ai.backend.manager.dto.user_config_input import (
    DeleteDefaultDotfileInput,
    UpdateDefaultDotfileInput,
)

STORED_PATH = "/etc/stored"


@pytest.fixture
def dotfile_processors() -> MagicMock:
    processors = MagicMock()
    processors.search.run = AsyncMock(return_value=MagicMock(items=[MagicMock(path=STORED_PATH)]))
    processors.update.run = AsyncMock()
    processors.purge.run = AsyncMock()
    return processors


@pytest.fixture
def adapter(dotfile_processors: MagicMock) -> UserConfigAdapter:
    return UserConfigAdapter(MagicMock(), dotfile_processors)


class TestStoredPathOutsideWorkDir:
    async def test_update_rejected(
        self, adapter: UserConfigAdapter, dotfile_processors: MagicMock
    ) -> None:
        with pytest.raises(InvalidDotfilePath):
            await adapter.update_default_dotfile(
                UpdateDefaultDotfileInput(
                    user_id=UserID(uuid.uuid4()), path=STORED_PATH, perm="644", data="x"
                )
            )
        dotfile_processors.update.run.assert_not_awaited()

    async def test_delete_allowed(
        self, adapter: UserConfigAdapter, dotfile_processors: MagicMock
    ) -> None:
        await adapter.delete_default_dotfile(
            DeleteDefaultDotfileInput(user_id=UserID(uuid.uuid4()), path=STORED_PATH)
        )
        dotfile_processors.purge.run.assert_awaited_once()
