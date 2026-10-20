"""The ``mgr image`` commands configure the ORM mappers from a minimal set of models."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.cli.types import ExitCode
from ai.backend.manager.cli import image_impl

_CONFIGURE_MAPPERS = f"""
from sqlalchemy.orm import configure_mappers

from {image_impl.__name__} import _register_image_cli_orm_cluster

_register_image_cli_orm_cluster()
configure_mappers()
"""


def test_the_registered_models_let_every_mapper_configure() -> None:
    # A fresh interpreter: other tests import every model, which hides a missing registration.
    result = subprocess.run(
        [sys.executable, "-c", _CONFIGURE_MAPPERS],
        env={**os.environ, "PYTHONPATH": os.pathsep.join(sys.path)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


@pytest.fixture
def rescan_result(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    result = MagicMock()
    result.errors = []

    @asynccontextmanager
    async def connect_database(_: Any) -> AsyncIterator[MagicMock]:
        yield MagicMock()

    cli_ctx = MagicMock()
    cli_ctx.get_bootstrap_config = AsyncMock()
    monkeypatch.setattr(image_impl, "connect_database", connect_database)
    monkeypatch.setattr(image_impl, "_register_image_cli_orm_cluster", lambda: None)
    monkeypatch.setattr(image_impl, "V2DBOpsProvider", MagicMock())
    db_source = MagicMock()
    db_source.return_value.rescan_images = AsyncMock(return_value=result)
    monkeypatch.setattr(image_impl, "ImageDBSource", db_source)
    result.cli_ctx = cli_ctx
    result.db_source = db_source
    return result


async def test_rescan_exits_zero_without_scan_errors(rescan_result: MagicMock) -> None:
    await image_impl.rescan_images(rescan_result.cli_ctx, "registry")


async def test_rescan_exits_non_zero_and_prints_the_scan_errors(
    rescan_result: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    rescan_result.errors = ["Failed to scan image! Detail: boom"]
    with pytest.raises(SystemExit) as exc_info:
        await image_impl.rescan_images(rescan_result.cli_ctx, "registry")
    assert exc_info.value.code == ExitCode.FAILURE
    assert "Failed to scan image! Detail: boom" in capsys.readouterr().err


async def test_rescan_exits_non_zero_when_the_scan_raises(
    rescan_result: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    rescan_result.db_source.return_value.rescan_images.side_effect = RuntimeError("down")
    with pytest.raises(SystemExit) as exc_info:
        await image_impl.rescan_images(rescan_result.cli_ctx, "registry")
    assert exc_info.value.code == ExitCode.FAILURE
    assert "down" in capsys.readouterr().err
