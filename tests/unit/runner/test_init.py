"""The PID-1 reaper that stands in for Docker's --init (tini) on the containerd backend.

Reaping is the kind of thing that looks right and silently does not work, so these exercise the
real script as a real process rather than mocking os.wait().

Being PID 1 is what normally makes orphans land on you, and a test cannot become PID 1 without a
PID namespace — which is not available in every sandbox, and a test that silently skips is worse
than no test. So the reaper also sets PR_SET_CHILD_SUBREAPER: orphaned descendants re-parent to it
whether or not it is PID 1. That is the same code path either way — an orphan arrives, and os.wait()
collects it — and it is what these drive.
"""

import ctypes
import ctypes.util
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

from ai.backend.runner import init as init_module

# Resolve through the module, not a path relative to the CWD: the test sandbox has a
# different working directory, and this also makes the dependency explicit.
_INIT = Path(init_module.__file__).resolve()

# Leaves an orphan behind: fork a child, have it fork a grandchild, then let the child exit first.
# The grandchild's parent is gone, so it re-parents to the nearest subreaper — and only that process
# can collect it. It reports the grandchild's pid so the test knows what to watch.
_ORPHAN_MAKER = """
import os, sys, time
pidfile = sys.argv[1]
child = os.fork()
if child == 0:
    grandchild = os.fork()
    if grandchild == 0:
        time.sleep(0.5)          # outlive our parent, so we end up orphaned
        os._exit(0)
    open(pidfile, "w").write(str(grandchild))
    os._exit(0)                  # our parent dies first -> the grandchild is orphaned
os.waitpid(child, 0)
time.sleep(3.0)                  # stay alive while the orphan dies and is (or is not) reaped
"""


def _is_zombie(pid: int) -> bool:
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return False  # the pid is gone entirely, so it was reaped
    return stat[stat.rfind(")") + 2] == "Z"


def _await_orphan_pid(proc: "subprocess.Popen[bytes]", pidfile: Path) -> int:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if pidfile.exists() and pidfile.read_text().strip():
            return int(pidfile.read_text().strip())
        time.sleep(0.05)
    proc.kill()
    raise AssertionError("the workload never reported its orphan's pid")


class TestReaping:
    def test_an_unreaped_orphan_becomes_a_zombie(self, tmp_path: Path) -> None:
        # Establishes that the problem is real. This harness stands in for the kernel runner as
        # PID 1: it is the subreaper, so the orphan lands on it — and it never calls wait(), so the
        # orphan sits there as a zombie holding a PID. That is today's containerd behaviour.
        pidfile = tmp_path / "orphan.pid"
        harness = textwrap.dedent("""
            import ctypes, ctypes.util, subprocess, sys, time
            libc = ctypes.CDLL(ctypes.util.find_library("c"))
            libc.prctl(36, 1, 0, 0, 0)          # PR_SET_CHILD_SUBREAPER: orphans land on us
            subprocess.Popen([sys.executable, "-c", sys.argv[1], sys.argv[2]]).wait()
            time.sleep(4.0)                      # ...and we never reap anything else
        """)
        proc = subprocess.Popen([sys.executable, "-c", harness, _ORPHAN_MAKER, str(pidfile)])
        try:
            orphan = _await_orphan_pid(proc, pidfile)
            time.sleep(1.5)  # the orphan has exited by now, and nobody has collected it
            assert _is_zombie(orphan), "expected the unreaped orphan to be left as a zombie"
        finally:
            proc.kill()
            proc.wait()

    def test_the_reaper_collects_the_orphan(self, tmp_path: Path) -> None:
        # Note the reaper is NOT PID 1 here — so this also proves PR_SET_CHILD_SUBREAPER took
        # effect: without it the orphan would re-parent past the reaper to the real init, and the
        # reaper would never see it.
        pidfile = tmp_path / "orphan.pid"
        proc = subprocess.Popen([
            sys.executable,
            str(_INIT),
            sys.executable,
            "-c",
            _ORPHAN_MAKER,
            str(pidfile),
        ])
        try:
            orphan = _await_orphan_pid(proc, pidfile)
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and _is_zombie(orphan):
                time.sleep(0.05)
            assert not _is_zombie(orphan), "the reaper left the orphan as a zombie"
        finally:
            proc.kill()
            proc.wait()


class TestExitStatus:
    def test_the_programs_exit_code_is_propagated(self) -> None:
        # The container's exit code must be the workload's, not the supervisor's.
        result = subprocess.run(
            [sys.executable, str(_INIT), sys.executable, "-c", "import sys; sys.exit(42)"],
            timeout=60,
        )
        assert result.returncode == 42

    def test_a_signalled_program_reports_128_plus_signum(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(_INIT),
                sys.executable,
                "-c",
                "import os, signal; os.kill(os.getpid(), signal.SIGTERM)",
            ],
            timeout=60,
        )
        assert result.returncode == 128 + signal.SIGTERM


class TestSignalForwarding:
    def test_a_signal_reaches_the_real_program(self) -> None:
        # The kernel runner traps SIGINT/SIGTERM to shut down cleanly. Once it is no longer PID 1
        # the signal arrives at the reaper, which has to pass it down — otherwise the graceful path
        # never runs and every kernel is SIGKILLed after its whole grace period.
        program = textwrap.dedent("""
            import signal, sys, time
            signal.signal(signal.SIGTERM, lambda s, f: sys.exit(7))
            print("READY", flush=True)
            time.sleep(60)
        """)
        proc = subprocess.Popen(
            [sys.executable, str(_INIT), sys.executable, "-u", "-c", program],
            stdout=subprocess.PIPE,
        )
        try:
            assert proc.stdout is not None
            assert proc.stdout.readline().strip() == b"READY"
            proc.send_signal(signal.SIGTERM)  # to the reaper, not to the program
            assert proc.wait(timeout=60) == 7  # the program's own handler ran
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


class TestDoesNotBreakAsyncioSubprocesses:
    def test_asyncio_still_gets_its_childrens_exit_codes(self) -> None:
        # This is why the reaper is a separate process and not a reaper inside the kernel runner.
        # The runner drives user code through asyncio.create_subprocess_exec, and asyncio collects
        # those children itself. A blanket waitpid(-1) in the same process would race it and steal
        # their exit statuses — the runner would lose the exit code of the very code it was asked
        # to run. As a child of the reaper, it keeps them.
        program = textwrap.dedent("""
            import asyncio

            async def main():
                codes = []
                for want in (0, 3, 42):
                    proc = await asyncio.create_subprocess_exec("sh", "-c", f"exit {want}")
                    codes.append(await proc.wait())
                print(codes, flush=True)

            asyncio.run(main())
        """)
        result = subprocess.run(
            [sys.executable, str(_INIT), sys.executable, "-u", "-c", program],
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.stdout.strip() == "[0, 3, 42]"


def test_libc_is_reachable() -> None:
    # Guards the assumption _become_subreaper() rests on.
    assert os.name == "posix"
    assert ctypes.util.find_library("c") is not None
