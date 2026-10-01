from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web

from ai.backend.agent.errors.watcher import (
    InvalidMountNameError,
    VolumeMountFailedError,
    VolumeUnmountFailedError,
)
from ai.backend.agent.watcher import handle_mount, handle_umount
from ai.backend.common.exception import BackendAIError

type _Handler = Callable[[web.Request], Awaitable[web.Response]]
type _RequestFactory = Callable[[str], web.Request]


@dataclass(frozen=True)
class _RejectedNameCase:
    name: str


@dataclass(frozen=True)
class _CommandFailureCase:
    handler: _Handler
    expected_error: type[BackendAIError]


class _FakeProcess:
    _stderr: bytes

    def __init__(self, stderr: bytes) -> None:
        self._stderr = stderr

    async def communicate(self) -> tuple[bytes, bytes]:
        return b"", self._stderr

    async def wait(self) -> int:
        return 0


@pytest.fixture
def mount_prefix(tmp_path: Path) -> Path:
    prefix = tmp_path / "mnt"
    prefix.mkdir()
    return prefix


@pytest.fixture
def escaping_symlink(tmp_path: Path, mount_prefix: Path) -> str:
    outside = tmp_path / "outside"
    outside.mkdir()
    (mount_prefix / "escape").symlink_to(outside)
    return "escape"


@pytest.fixture
def executed_commands(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, ...]]:
    commands: list[tuple[str, ...]] = []

    async def fake_exec(*args: str, **kwargs: Any) -> _FakeProcess:
        commands.append(args)
        return _FakeProcess(stderr=b"")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    return commands


@pytest.fixture
def failing_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_exec(*args: str, **kwargs: Any) -> _FakeProcess:
        return _FakeProcess(stderr=b"mount: permission denied")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)


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
            _RejectedNameCase(name=""),
            _RejectedNameCase(name="."),
            _RejectedNameCase(name=".."),
            _RejectedNameCase(name="../outside"),
            _RejectedNameCase(name="vol/../../outside"),
            _RejectedNameCase(name="/etc"),
        ],
        ids=lambda case: case.name or "<empty>",
    )
    async def test_rejects_name_outside_mount_prefix(
        self,
        make_request: _RequestFactory,
        executed_commands: list[tuple[str, ...]],
        tmp_path: Path,
        mount_prefix: Path,
        handler: _Handler,
        case: _RejectedNameCase,
    ) -> None:
        with pytest.raises(InvalidMountNameError):
            await handler(make_request(case.name))

        assert executed_commands == []
        assert list(tmp_path.iterdir()) == [mount_prefix]

    @pytest.mark.parametrize(
        "handler", [handle_mount, handle_umount], ids=lambda handler: handler.__name__
    )
    async def test_rejects_symlink_leaving_mount_prefix(
        self,
        make_request: _RequestFactory,
        executed_commands: list[tuple[str, ...]],
        escaping_symlink: str,
        handler: _Handler,
    ) -> None:
        with pytest.raises(InvalidMountNameError):
            await handler(make_request(escaping_symlink))

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

    async def test_unmounts_name_under_mount_prefix(
        self,
        make_request: _RequestFactory,
        executed_commands: list[tuple[str, ...]],
        mount_prefix: Path,
    ) -> None:
        resp = await handle_umount(make_request("vol1"))

        assert resp.status == 200
        assert executed_commands == [("sudo", "umount", str(mount_prefix / "vol1"))]


class TestMountCommandFailure:
    @pytest.mark.parametrize(
        "case",
        [
            _CommandFailureCase(handler=handle_mount, expected_error=VolumeMountFailedError),
            _CommandFailureCase(handler=handle_umount, expected_error=VolumeUnmountFailedError),
        ],
        ids=lambda case: case.handler.__name__,
    )
    async def test_raises_when_command_writes_stderr(
        self,
        make_request: _RequestFactory,
        failing_commands: None,
        case: _CommandFailureCase,
    ) -> None:
        with pytest.raises(case.expected_error) as exc_info:
            await case.handler(make_request("vol1"))

        assert exc_info.value.extra_msg == "mount: permission denied"
