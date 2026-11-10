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
from ai.backend.agent.watcher import handle_fstab_detail, handle_mount, handle_umount

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

    @pytest.mark.usefixtures("executed_commands")
    async def test_mounts_name_under_mount_prefix(
        self,
        make_request: _RequestFactory,
        mount_prefix: Path,
    ) -> None:
        resp = await handle_mount(make_request("vol1"))

        assert resp.status == 200
        assert (mount_prefix / "vol1").is_dir()


class TestFstabPath:
    @pytest.fixture
    def configured_fstab(self, tmp_path: Path) -> Path:
        path = tmp_path / "configured-fstab"
        path.write_text("configured\n")
        return path

    @pytest.fixture
    def requested_file(self, tmp_path: Path) -> Path:
        path = tmp_path / "requested-file"
        path.write_text("requested\n")
        return path

    @pytest.fixture
    def watcher_app(self, mount_prefix: Path, configured_fstab: Path) -> dict[str, Any]:
        config_server = AsyncMock()
        config_server.get.return_value = str(mount_prefix)
        return {
            "config_server": config_server,
            "config": {"watcher": {"fstab-path": str(configured_fstab)}},
        }

    def _edit_request(
        self, watcher_app: dict[str, Any], fstab_path: Path | None, name: str = "vol1"
    ) -> web.Request:
        request = MagicMock(spec=web.Request)
        request.app = watcher_app
        request.json = AsyncMock(
            return_value={
                "name": name,
                "fs_type": "nfs",
                "fs_location": "host:/x",
                "options": None,
                "edit_fstab": True,
                "fstab_path": str(fstab_path) if fstab_path is not None else None,
            }
        )
        return request

    async def test_detail_reads_configured_path_regardless_of_query(
        self,
        watcher_app: dict[str, Any],
        requested_file: Path,
    ) -> None:
        request = MagicMock(spec=web.Request)
        request.app = watcher_app
        request.query = {"fstab_path": str(requested_file)}

        resp = await handle_fstab_detail(request)

        assert resp.text == "configured\n"

    @pytest.mark.usefixtures("executed_commands")
    async def test_mount_edits_configured_path_regardless_of_body(
        self,
        watcher_app: dict[str, Any],
        configured_fstab: Path,
        requested_file: Path,
    ) -> None:
        await handle_mount(self._edit_request(watcher_app, requested_file))

        assert "host:/x" in configured_fstab.read_text()
        assert requested_file.read_text() == "requested\n"

    @pytest.mark.usefixtures("executed_commands")
    async def test_mount_edits_configured_path_without_fstab_path_in_body(
        self,
        watcher_app: dict[str, Any],
        configured_fstab: Path,
    ) -> None:
        await handle_mount(self._edit_request(watcher_app, None))

        assert "host:/x" in configured_fstab.read_text()

    @pytest.mark.usefixtures("executed_commands")
    async def test_umount_edits_configured_path_regardless_of_body(
        self,
        watcher_app: dict[str, Any],
        mount_prefix: Path,
        configured_fstab: Path,
        requested_file: Path,
    ) -> None:
        entry = f"host:/x {mount_prefix / 'vol1'} nfs defaults 0 0\n"
        configured_fstab.write_text(entry)
        requested_file.write_text(entry)

        await handle_umount(self._edit_request(watcher_app, requested_file))

        assert configured_fstab.read_text() == ""
        assert requested_file.read_text() == entry
