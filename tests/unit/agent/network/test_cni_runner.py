import asyncio
import json
import os
from pathlib import Path
from typing import Any

import pytest

from ai.backend.agent.network.cni_runner import (
    CniError,
    CniPluginRunner,
    build_cni_env,
    netns_path_for_pid,
    resolve_plugin_binary,
)

_CONFIG = {"cniVersion": "1.0.0", "name": "bai-overlay", "type": "bridge", "bridge": "baibr4097"}


class FakeProc:
    def __init__(self, returncode: int, stdout: bytes = b"", stderr: bytes = b"") -> None:
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self.stdin_data: bytes | None = None

    async def communicate(self, data: bytes | None = None) -> tuple[bytes, bytes]:
        self.stdin_data = data
        return self._stdout, self._stderr


def _patch_exec(monkeypatch: pytest.MonkeyPatch, proc: FakeProc) -> dict[str, Any]:
    captured: dict[str, Any] = {}

    async def fake_exec(binary: str, **kwargs: Any) -> FakeProc:
        captured["binary"] = binary
        captured["env"] = kwargs.get("env")
        captured["proc"] = proc
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    return captured


class TestHelpers:
    def test_netns_path_for_pid(self) -> None:
        assert netns_path_for_pid(1234) == "/proc/1234/ns/net"

    def test_build_cni_env(self) -> None:
        env = build_cni_env(
            "ADD", container_id="c1", netns="/proc/1/ns/net", ifname="baimulti0",
            cni_path="/opt/cni/bin",
        )
        assert env["CNI_COMMAND"] == "ADD"
        assert env["CNI_CONTAINERID"] == "c1"
        assert env["CNI_NETNS"] == "/proc/1/ns/net"
        assert env["CNI_IFNAME"] == "baimulti0"
        assert env["CNI_PATH"] == "/opt/cni/bin"

    def test_resolve_binary_prefers_existing(self, tmp_path: Path) -> None:
        binary = tmp_path / "bridge"
        binary.write_text("#!/bin/sh\n")
        assert resolve_plugin_binary("bridge", str(tmp_path)) == str(binary)

    def test_resolve_binary_falls_back_to_first_dir(self, tmp_path: Path) -> None:
        result = resolve_plugin_binary("bridge", str(tmp_path))
        assert result == os.path.join(str(tmp_path), "bridge")


class TestCniPluginRunner:
    async def test_add_passes_env_and_stdin_and_parses_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        result_json = json.dumps({"cniVersion": "1.0.0", "ips": [{"address": "10.128.5.5/24"}]})
        proc = FakeProc(0, stdout=result_json.encode())
        captured = _patch_exec(monkeypatch, proc)

        runner = CniPluginRunner(cni_path="/opt/cni/bin")
        result = await runner(
            "ADD", ifname="baimulti0", netns="/proc/1/ns/net",
            container_id="c1", config=_CONFIG,
        )
        assert result is not None
        assert result["ips"][0]["address"] == "10.128.5.5/24"
        assert captured["env"]["CNI_COMMAND"] == "ADD"
        assert captured["env"]["CNI_IFNAME"] == "baimulti0"
        # config was written to stdin
        assert json.loads(proc.stdin_data) == _CONFIG

    async def test_del_with_empty_output_returns_none(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        proc = FakeProc(0, stdout=b"")
        _patch_exec(monkeypatch, proc)
        runner = CniPluginRunner()
        result = await runner(
            "DEL", ifname="baimulti0", netns="/proc/1/ns/net",
            container_id="c1", config=_CONFIG,
        )
        assert result is None

    async def test_nonzero_exit_raises_cni_error_with_detail(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        err_json = json.dumps({"code": 100, "msg": "bridge not found"})
        proc = FakeProc(1, stdout=err_json.encode())
        _patch_exec(monkeypatch, proc)
        runner = CniPluginRunner()
        with pytest.raises(CniError) as exc:
            await runner(
                "ADD", ifname="baimulti0", netns="/proc/1/ns/net",
                container_id="c1", config=_CONFIG,
            )
        assert "bridge not found" in str(exc.value)
