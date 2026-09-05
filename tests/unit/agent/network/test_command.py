"""One way to run a privileged command, and one way to give up on it.

The privnet runs these under a node-wide barrier, so an invocation that never returns stops every
attach, teardown and peer update on the host. Each caller used to spawn its own subprocess and so
was a separate chance to forget the deadline -- three of them had.
"""

from __future__ import annotations

import asyncio

import pytest

from ai.backend.agent.network import command


class _Wedged:
    """A command that never finishes, and remembers whether it was killed."""

    def __init__(self) -> None:
        self.returncode: int | None = None
        self.killed = False

    async def communicate(self) -> tuple[bytes, bytes]:
        await asyncio.Event().wait()
        raise AssertionError("unreachable")

    def kill(self) -> None:
        self.killed = True

    async def wait(self) -> int:
        return -9


def _spawning(proc: _Wedged, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _spawn(*argv: str, **kwargs: object) -> _Wedged:
        return proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", _spawn)


class TestACommandPastItsDeadline:
    async def test_it_is_killed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        proc = _Wedged()
        _spawning(proc, monkeypatch)
        monkeypatch.setattr(command, "DEFAULT_TIMEOUT_SEC", 0.05)
        with pytest.raises(command.CommandTimeout):
            await command.run(["ip", "link", "show"])
        assert proc.killed, "it was left running against a host whose lock has moved on"

    async def test_the_message_names_the_deadline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _spawning(_Wedged(), monkeypatch)
        monkeypatch.setattr(command, "DEFAULT_TIMEOUT_SEC", 0.05)
        with pytest.raises(command.CommandTimeout, match="0s"):
            await command.run(["ip", "link", "show"])


class TestACommandCancelledFromOutside:
    """A request deadline or a shutdown reaches a command already in flight. Left alone, it goes on
    changing the host after the lock that authorised it has been given to somebody else."""

    async def test_it_is_killed_too(self, monkeypatch: pytest.MonkeyPatch) -> None:
        proc = _Wedged()
        _spawning(proc, monkeypatch)
        task = asyncio.create_task(command.run(["ip", "link", "show"]))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert proc.killed


class TestACommandThatFinishes:
    async def test_its_output_comes_back(self, monkeypatch: pytest.MonkeyPatch) -> None:
        class _Quick:
            returncode = 0

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"out", b"err"

        async def _spawn(*argv: str, **kwargs: object) -> _Quick:
            return _Quick()

        monkeypatch.setattr(asyncio, "create_subprocess_exec", _spawn)
        assert await command.run(["true"]) == (0, b"out", b"err")

    async def test_a_failure_is_the_callers_to_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # The runner reports the code; what a non-zero one MEANS differs per caller, so it does
        # not raise here.
        class _Failing:
            returncode = 2

            async def communicate(self) -> tuple[bytes, bytes]:
                return b"", b"nope"

        async def _spawn(*argv: str, **kwargs: object) -> _Failing:
            return _Failing()

        monkeypatch.setattr(asyncio, "create_subprocess_exec", _spawn)
        assert (await command.run(["false"]))[0] == 2
