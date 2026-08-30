"""A busy aiomonitor port must not stop the agent from starting."""

from __future__ import annotations

import socket
from types import SimpleNamespace
from typing import Any

import aiomonitor
import pytest

import ai.backend.agent.server as server_mod
from ai.backend.agent.server import _port_is_free, aiomonitor_ctx


class TestPortPreflight:
    def test_a_bound_port_reads_as_busy(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            s.listen(1)
            port = s.getsockname()[1]
            assert _port_is_free(port) is False

    def test_the_same_port_reads_as_free_once_released(self) -> None:
        """Paired with the case above so the probe is shown to answer the question asked, rather
        than always saying "busy"."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]
        assert _port_is_free(port) is True


class TestABusyPortIsSkipped:
    """`Monitor.start()` raises on its own thread when the bind fails, so the `except` around it
    never fires and startup HANGS — the agent stops right after "Using uvloop" and never
    registers. Two agents on one host share the default ports, which is the normal multi-backend
    layout, so this is the common case rather than a corner one."""

    async def test_it_does_not_start_the_monitor_on_a_busy_port(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        started: list[str] = []

        class _Monitor:
            prompt = ""
            console_locals: dict[str, Any] = {}

            def __init__(self, *a: Any, **kw: Any) -> None:
                pass

            def start(self) -> None:
                started.append("start")

            def close(self) -> None:
                started.append("close")

        monkeypatch.setattr(aiomonitor, "Monitor", _Monitor)
        monkeypatch.setattr(server_mod, "Profiler", lambda **kw: None)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as taken:
            taken.bind(("127.0.0.1", 0))
            taken.listen(1)
            busy_port = taken.getsockname()[1]
            cfg = _config(termui=busy_port, webui=busy_port + 1)
            async with aiomonitor_ctx(cfg, 0):
                pass

        assert started == [], "the monitor must not be started when its port is taken"

    async def test_it_starts_when_the_ports_are_free(self, monkeypatch: pytest.MonkeyPatch) -> None:
        started: list[str] = []

        class _Monitor:
            prompt = ""
            console_locals: dict[str, Any] = {}

            def __init__(self, *a: Any, **kw: Any) -> None:
                pass

            def start(self) -> None:
                started.append("start")

            def close(self) -> None:
                started.append("close")

        monkeypatch.setattr(aiomonitor, "Monitor", _Monitor)
        monkeypatch.setattr(server_mod, "Profiler", lambda **kw: None)

        # BOTH ports are taken from the kernel and released. `free + 1` used to stand in for the
        # second one, which is a port nothing guarantees is free — and one busy port is exactly
        # what makes this test's expectation false.
        with (
            socket.socket(socket.AF_INET, socket.SOCK_STREAM) as a,
            socket.socket(socket.AF_INET, socket.SOCK_STREAM) as b,
        ):
            a.bind(("127.0.0.1", 0))
            b.bind(("127.0.0.1", 0))
            termui, webui = a.getsockname()[1], b.getsockname()[1]
        cfg = _config(termui=termui, webui=webui)
        async with aiomonitor_ctx(cfg, 0):
            pass

        assert started == ["start", "close"]


def _config(*, termui: int, webui: int) -> Any:
    return SimpleNamespace(
        agent_common=SimpleNamespace(aiomonitor_termui_port=termui, aiomonitor_webui_port=webui),
        debug=SimpleNamespace(enhanced_aiomonitor_task_info=False),
        pyroscope=SimpleNamespace(enabled=False, app_name="x", server_addr="", sample_rate=1),
    )
