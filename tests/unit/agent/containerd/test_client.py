"""The agent's client maps the client package's errors to agent errors."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from ai.backend.agent.containerd.client import ContainerdClient, ContainerdClientConfig
from ai.backend.agent.containerd.rpc import errors as rpc_errors
from ai.backend.agent.containerd.rpc import types as rpc_types
from ai.backend.agent.errors.containerd import (
    ContainerdOperationFailed,
    ContainerdUnavailableError,
)


def _client_raising(monkeypatch: pytest.MonkeyPatch, method: str, error: Exception) -> Any:
    client = ContainerdClient(
        ContainerdClientConfig(address="/nonexistent.sock", namespace="ns", snapshotter="overlayfs")
    )
    monkeypatch.setattr(client._client, method, AsyncMock(side_effect=error))
    return client


@pytest.mark.parametrize(
    ("method", "args", "error", "expected"),
    [
        ("connect", (), rpc_errors.ContainerdUnavailable("down"), ContainerdUnavailableError),
        (
            "list_containers",
            ({},),
            rpc_errors.ContainerdCallFailed("list_containers", "INTERNAL", "boom"),
            ContainerdOperationFailed,
        ),
    ],
)
async def test_package_errors_become_agent_errors(
    monkeypatch: pytest.MonkeyPatch,
    method: str,
    args: tuple[Any, ...],
    error: Exception,
    expected: type[Exception],
) -> None:
    client = _client_raising(monkeypatch, method, error)

    with pytest.raises(expected) as exc_info:
        await getattr(client, method)(*args)

    assert exc_info.value.__cause__ is error
    assert str(error) in str(exc_info.value)


async def test_results_pass_through(monkeypatch: pytest.MonkeyPatch) -> None:
    task = rpc_types.TaskInfo(pid=7, state=rpc_types.TaskState.RUNNING, exit_status=0)
    client = ContainerdClient(
        ContainerdClientConfig(address="/nonexistent.sock", namespace="ns", snapshotter="overlayfs")
    )
    monkeypatch.setattr(client._client, "get_task", AsyncMock(return_value=task))

    assert await client.get_task("c") is task
    assert not client.connected
