from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.agent.errors.watcher import InvalidMountNameError
from ai.backend.agent.watcher import handle_mount, handle_umount

type _Handler = Callable[[web.Request], Awaitable[web.Response]]
type _RequestFactory = Callable[[str], web.Request]


@dataclass(frozen=True)
class _RejectedNameCase:
    name: str


class _FakeProcess:
    async def communicate(self) -> tuple[bytes, bytes]:
        return b"", b""

    async def wait(self) -> int:
        return 0


@pytest.fixture
def mount_prefix(tmp_path: Path) -> Path:
    prefix = tmp_path / "mnt"
    prefix.mkdir()
    return prefix


@pytest.fixture
def executed_commands(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, ...]]:
    commands: list[tuple[str, ...]] = []

    async def fake_exec(*args: str, **kwargs: Any) -> _FakeProcess:
        commands.append(args)
        return _FakeProcess()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    return commands


@pytest.fixture
def make_request(mount_prefix: Path) -> _RequestFactory:
    config_server = AsyncMock()
    config_server.get.return_value = str(mount_prefix)

    def factory(name: str) -> web.Request:
        request = MagicMock(spec=web.Request)
        request.app = {"config_server": config_server}
        request.json = AsyncMock(
            return_value={
                "name": name,
                "fs_type": "nfs",
                "fs_location": "host:/x",
                "edit_fstab": False,
            }
        )
        return request

    return factory


class TestMountNameValidation:
    @pytest.mark.parametrize(
        "handler", [handle_mount, handle_umount], ids=lambda handler: handler.__name__
    )
    @pytest.mark.parametrize(
        "case",
        [
            _RejectedNameCase(name="../outside"),
            _RejectedNameCase(name="/etc"),
        ],
        ids=lambda case: case.name,
    )
    async def test_rejects_name_outside_mount_prefix(
        self,
        make_request: _RequestFactory,
        executed_commands: list[tuple[str, ...]],
        handler: _Handler,
        case: _RejectedNameCase,
    ) -> None:
        with pytest.raises(InvalidMountNameError):
            await handler(make_request(case.name))

        assert executed_commands == []

    async def test_mounts_name_under_mount_prefix(
        self,
        make_request: _RequestFactory,
        executed_commands: list[tuple[str, ...]],
        mount_prefix: Path,
    ) -> None:
        resp = await handle_mount(make_request("vol1"))

        assert resp.status == 200
        assert executed_commands == [
            ("sudo", "mount", "-t", "nfs", "host:/x", str(mount_prefix / "vol1"))
        ]
