from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.events.event_types.session.anycast import SessionFailureAnycastEvent
from ai.backend.common.types import SessionId
from ai.backend.kube.gateway import kernels as kernels_module
from ai.backend.kube.gateway.errors import KernelFileNotFoundError, KernelPathNotAllowedError
from ai.backend.kube.gateway.kernel_index import KernelIndex
from ai.backend.kube.gateway.kernels import GatewayKernels
from ai.backend.kube.gateway.pod_exec import ExecResult

KERNEL_ID = "00000000-0000-0000-0000-000000000001"


SESSION_ID = str(uuid4())


def _pod() -> dict[str, Any]:
    return {
        "metadata": {
            "name": "s-1-main1",
            "namespace": "bai-p",
            "uid": "pod-uid",
            "labels": {"backend.ai/kernel-id": KERNEL_ID, "backend.ai/session-id": SESSION_ID},
            "annotations": {"backend.ai/kernel-uid": "1000", "backend.ai/kernel-gid": "1000"},
            "ownerReferences": [
                {
                    "apiVersion": "backend.ai/v1alpha1",
                    "kind": "SessionWorkload",
                    "name": "s-1",
                    "uid": "sw-uid",
                }
            ],
        },
        "spec": {"containers": [{"name": "kernel"}]},
        "status": {"podIP": "10.0.0.5", "phase": "Running"},
    }


class _Exec:
    result: ExecResult
    commands: list[list[str]]

    def __init__(self, result: ExecResult) -> None:
        self.result = result
        self.commands = []

    async def __call__(
        self,
        core: Any,
        ns: str,
        pod: str,
        container: str,
        command: list[str],
        *args: Any,
        **kwargs: Any,
    ) -> ExecResult:
        self.commands.append(command)
        return self.result


@pytest.fixture
def producer() -> MagicMock:
    producer = MagicMock()
    producer.anycast_event = AsyncMock()
    producer.anycast_and_broadcast_event = AsyncMock()
    return producer


@pytest.fixture
def kernels(producer: MagicMock) -> GatewayKernels:
    index = KernelIndex()
    index.replace_namespaces([
        {
            "metadata": {
                "name": "bai-p",
                "labels": {"app.kubernetes.io/managed-by": "backendai-manager"},
            }
        }
    ])
    index.replace_workloads([
        {
            "metadata": {"name": "s-1", "namespace": "bai-p", "uid": "sw-uid"},
            "spec": {"sessionId": SESSION_ID, "kernels": [{"kernelId": KERNEL_ID}]},
        }
    ])
    index.apply("ADDED", _pod())
    return GatewayKernels(index, MagicMock(), MagicMock(), producer)


def _exec(monkeypatch: pytest.MonkeyPatch, result: ExecResult) -> _Exec:
    fake = _Exec(result)
    monkeypatch.setattr(kernels_module, "exec_in_pod", fake)
    return fake


class TestFileScripts:
    async def test_scripts_run_isolated_as_the_kernel_user(
        self, kernels: GatewayKernels, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = _exec(monkeypatch, ExecResult(b"[]", b"", 0))
        await kernels.list_files(KERNEL_ID, ".")
        [command] = fake.commands
        assert command[:5] == [
            "/opt/kernel/su-exec",
            "1000:1000",
            "/opt/backend.ai/bin/python",
            "-I",
            "-c",
        ]

    async def test_list_files_reports_errors_as_the_agent_does(
        self, kernels: GatewayKernels, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _exec(monkeypatch, ExecResult(b"", b"No such file", 1))
        result = await kernels.list_files(KERNEL_ID, "missing")
        assert result == {"files": "", "errors": "No such file", "abspath": "missing"}

    async def test_a_path_outside_the_home_is_refused_before_exec(
        self, kernels: GatewayKernels, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake = _exec(monkeypatch, ExecResult(b"", b"", 0))
        with pytest.raises(KernelPathNotAllowedError):
            await kernels.download_file(KERNEL_ID, "../../etc/passwd")
        assert fake.commands == []

    async def test_a_missing_file_is_not_found(
        self, kernels: GatewayKernels, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _exec(monkeypatch, ExecResult(b"", b"no such file", 4))
        with pytest.raises(KernelFileNotFoundError):
            await kernels.download_single(KERNEL_ID, "x")


class TestBatch:
    async def test_an_unexpected_error_ends_the_batch_as_failed(
        self, kernels: GatewayKernels, producer: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(kernels, "execute", AsyncMock(side_effect=RuntimeError("boom")))
        session_id = SessionId(uuid4())
        await kernels._run_batch(session_id, KERNEL_ID, "run", None)
        [anycast, _] = producer.anycast_and_broadcast_event.await_args.args
        assert isinstance(anycast, SessionFailureAnycastEvent)
