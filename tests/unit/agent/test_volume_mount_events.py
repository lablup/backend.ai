from __future__ import annotations

import asyncio
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ai.backend.agent.agent import AbstractAgent, handle_volume_mount, handle_volume_umount
from ai.backend.common.events.event_types.volume.broadcast import (
    DoVolumeMountEvent,
    DoVolumeUnmountEvent,
)
from ai.backend.common.types import AgentId, QuotaScopeID, QuotaScopeType


class _FakeProcess:
    async def communicate(self) -> tuple[bytes, bytes]:
        return b"", b""

    async def wait(self) -> int:
        return 0


@pytest.fixture
def quota_scope_id() -> QuotaScopeID:
    return QuotaScopeID(QuotaScopeType.USER, uuid4())


@pytest.fixture
def event_fstab(tmp_path: Path) -> Path:
    path = tmp_path / "event-fstab"
    path.write_text("unchanged\n")
    return path


@pytest.fixture
def context(tmp_path: Path) -> AbstractAgent[Any, Any]:
    etcd = AsyncMock()
    etcd.get.side_effect = lambda key: str(tmp_path) if key == "volumes/_mount" else None
    local_config = MagicMock()
    local_config.agent.cohabiting_storage_proxy = False
    local_config.agent.mount_path_uid_gid = None
    local_config.agent.real_mount_path.return_value = tmp_path / "vol1"
    return cast(
        AbstractAgent[Any, Any],
        SimpleNamespace(
            id=AgentId("i-test"),
            etcd=etcd,
            local_config=local_config,
            event_producer=AsyncMock(),
        ),
    )


@pytest.fixture
def opened_fstab_paths(monkeypatch: pytest.MonkeyPatch) -> Iterator[list[str]]:
    async def fake_exec(*_args: str, **_kwargs: Any) -> _FakeProcess:
        return _FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    paths: list[str] = []

    def fake_open(path: str, **_kwargs: Any) -> MagicMock:
        paths.append(path)
        return MagicMock(__aenter__=AsyncMock(), __aexit__=AsyncMock(return_value=False))

    fstab = MagicMock(add=AsyncMock(), remove_by_mountpoint=AsyncMock())
    with (
        patch("ai.backend.common.utils.aiofiles.open", fake_open),
        patch("ai.backend.common.utils.Fstab", return_value=fstab),
    ):
        yield paths


class TestVolumeEventFstabPath:
    async def test_mount_edits_system_fstab_regardless_of_event_path(
        self,
        context: AbstractAgent[Any, Any],
        quota_scope_id: QuotaScopeID,
        event_fstab: Path,
        opened_fstab_paths: list[str],
    ) -> None:
        event = DoVolumeMountEvent(
            dir_name="vol1",
            volume_backend_name="backend",
            quota_scope_id=quota_scope_id,
            fs_location="host:/x",
            edit_fstab=True,
            fstab_path=str(event_fstab),
        )

        await handle_volume_mount(context, AgentId("manager"), event)

        assert opened_fstab_paths == ["/etc/fstab"]
        assert event_fstab.read_text() == "unchanged\n"

    async def test_umount_edits_system_fstab_regardless_of_event_path(
        self,
        context: AbstractAgent[Any, Any],
        quota_scope_id: QuotaScopeID,
        event_fstab: Path,
        opened_fstab_paths: list[str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(Path, "is_mount", lambda _self: True)
        event = DoVolumeUnmountEvent(
            dir_name="vol1",
            volume_backend_name="backend",
            quota_scope_id=quota_scope_id,
            edit_fstab=True,
            fstab_path=str(event_fstab),
        )

        await handle_volume_umount(context, AgentId("manager"), event)

        assert opened_fstab_paths == ["/etc/fstab"]
        assert event_fstab.read_text() == "unchanged\n"
