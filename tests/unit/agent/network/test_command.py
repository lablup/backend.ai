"""One way to run a privileged command, and one way to give up on it.

The privnet runs these under a node-wide barrier, so an invocation that never returns stops every
attach, teardown and peer update on the host. Each caller used to spawn its own subprocess and so
was a separate chance to forget the deadline -- three of them had.
"""

from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

from ai.backend.agent.errors.network import NetworkOperationFailed
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


class TestNoHandlerCatchesTheWrongThing:
    """The dead-handler sweep, kept swept.

    `_run`/`_runner` raise `NetworkOperationFailed`, which is a `BackendAIError` and therefore
    neither a `RuntimeError` nor an `OSError`. A handler written as `except (RuntimeError,
    OSError)` around a command call is dead code, and it disabled every absence and idempotency
    guard it was written to provide: session setup could not delete its own leftovers, and a
    container teardown retried `ip link del` on a veth that was already gone, forever. Both were
    found on live nodes, twice, so the shape is checked and not the instances.

    Only `try` blocks that actually run a host command are examined -- `except OSError` around a
    socket bind or a /proc read is right, and a sweep that flagged those would be turned off.
    """

    #: Names that mean "run a host command and raise if it failed". `command.run` is deliberately
    #: absent: it hands back the return code instead of raising, so `except OSError` around it
    #: (the binary missing before exec) is right and complete.
    _RUNNERS = frozenset({"_run", "_runner", "_remove", "runner"})

    @staticmethod
    def _runs_a_command(node: ast.Try, runners: frozenset[str]) -> bool:
        for child in ast.walk(ast.Module(body=node.body, type_ignores=[])):
            if not isinstance(child, ast.Call):
                continue
            func = child.func
            name = (
                func.attr
                if isinstance(func, ast.Attribute)
                else func.id
                if isinstance(func, ast.Name)
                else ""
            )
            if name in runners:
                return True
        return False

    @staticmethod
    def _suppressed_names(node: ast.With) -> set[str] | None:
        """The exception names a ``with contextlib.suppress(...)`` swallows, or None if this
        ``with`` is not one. Checked alongside `except`: it is the same handler written the other
        way, and the one instance of this bug that a search for `except` did not find sat here --
        the drift pass could not restore a flushed firewall chain because the delete it does first
        raised what the suppression did not name."""
        for item in node.items:
            call = item.context_expr
            if not isinstance(call, ast.Call):
                continue
            func = ast.unparse(call.func)
            if func in ("contextlib.suppress", "suppress"):
                return {ast.unparse(a) for a in call.args}
        return None

    @staticmethod
    def _names_of(handler: ast.ExceptHandler) -> set[str]:
        if handler.type is None:
            return {"BaseException"}
        parts = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
        return {ast.unparse(part) for part in parts}

    def test_every_handler_around_a_command_can_catch_what_it_raises(self) -> None:
        root = Path(__file__).resolve().parents[4] / "src/ai/backend/agent/network"
        offenders: list[str] = []
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if not isinstance(node, ast.Try):
                    continue
                if not self._runs_a_command(node, self._RUNNERS):
                    continue
                for handler in node.handlers:
                    names = self._names_of(handler)
                    if names <= {"RuntimeError", "OSError"}:
                        offenders.append(
                            f"{path.relative_to(root)}:{handler.lineno}: "
                            f"except {', '.join(sorted(names))}"
                        )
            for node in ast.walk(tree):
                if not isinstance(node, ast.With):
                    continue
                suppressed = self._suppressed_names(node)
                if suppressed is None or not suppressed <= {"RuntimeError", "OSError"}:
                    continue
                if self._runs_a_command(
                    ast.Try(body=node.body, handlers=[], orelse=[], finalbody=[]), self._RUNNERS
                ):
                    offenders.append(
                        f"{path.relative_to(root)}:{node.lineno}: "
                        f"contextlib.suppress({', '.join(sorted(suppressed))})"
                    )
        assert not offenders, (
            "these handlers sit on a host command but cannot catch NetworkOperationFailed, so"
            " they are dead code; use `command.HOST_COMMAND_ERRORS`:\n" + "\n".join(offenders)
        )

    def test_the_tuple_covers_what_a_command_actually_raises(self) -> None:
        assert issubclass(NetworkOperationFailed, command.HOST_COMMAND_ERRORS)
        assert not issubclass(NetworkOperationFailed, (RuntimeError, OSError)), (
            "if this ever becomes true the bug class is gone and this suite can go with it"
        )
