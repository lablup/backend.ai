"""Container logs, written and rotated the way Docker's log driver does.

Docker does not let the container write its own log: dockerd owns the write end of stdout and runs a
log driver over it, which is what makes max-size/max-file rotation a hard guarantee rather than a
best effort. containerd offers the same thing through a `binary://` log URI — it starts our writer
and pipes the container's output into it — and these drive that writer through containerd's actual
contract (fd 3 = stdout, fd 4 = stderr, fd 5 = a ready pipe), because the contract is the part that
would silently not work.
"""

import os
import sys
from pathlib import Path

from ai.backend.agent.containerd import log_writer
from ai.backend.agent.containerd.log_writer import (
    LOG_FILE_COUNT,
    RotatingLog,
    max_file_size,
    rotated_path,
)
from ai.backend.agent.containerd.logs import (
    logger_uri,
    read_log_tail,
    rotated_paths,
    unlink_log_files,
    write_logger_launcher,
)


def _run_logger(tmp_path: Path, container_id: str, max_length: int, chunks: list[bytes]) -> None:
    """Start the writer exactly as containerd's binaryIO does, feed it, and wait for it to finish."""
    writer = Path(log_writer.__file__).resolve()
    out_r, out_w = os.pipe()
    err_r, err_w = os.pipe()
    ready_r, ready_w = os.pipe()

    pid = os.fork()
    if pid == 0:  # pragma: no cover - the child execs away
        os.dup2(out_r, 3)
        os.dup2(err_r, 4)
        os.dup2(ready_w, 5)
        for fd in (3, 4, 5):
            os.set_inheritable(fd, True)
        os.environ["CONTAINER_ID"] = container_id
        os.execv(
            sys.executable,
            [
                sys.executable,
                str(writer),
                "--log-root",
                str(tmp_path),
                "--max-length",
                str(max_length),
            ],
        )
    os.close(out_r)
    os.close(err_r)
    os.close(ready_w)

    # containerd holds the task in 'created' until the writer closes this: the container must not be
    # able to write before someone is there to take its output.
    assert os.read(ready_r, 1) == b"", "the writer never signalled that it was ready"
    os.close(ready_r)

    for chunk in chunks:
        os.write(out_w, chunk)
    os.close(out_w)
    os.close(err_w)
    _pid, status = os.waitpid(pid, 0)
    assert os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0


class TestTheContainerdContract:
    def test_it_signals_ready_and_then_captures_the_output(self, tmp_path: Path) -> None:
        _run_logger(tmp_path, "kern-1", 10_000, [b"hello ", b"world"])
        assert read_log_tail(tmp_path / "kern-1.log", 10_000) == b"hello world"

    def test_the_cap_is_hard(self, tmp_path: Path) -> None:
        # The point of owning the write end. The old approach swept the file on a timer, so a burst
        # between two ticks overshot the budget; here no write can take the log past it, because we
        # are the one performing the write.
        _run_logger(tmp_path, "kern-1", 10_000, [b"X" * 100] * 300)  # 30 KB into a 10 KB budget

        sizes = {p.name: p.stat().st_size for p in tmp_path.iterdir()}
        assert sum(sizes.values()) <= 10_000
        assert all(size <= max_file_size(10_000) for size in sizes.values())
        assert len(sizes) <= LOG_FILE_COUNT

    def test_it_keeps_the_newest_output(self, tmp_path: Path) -> None:
        _run_logger(tmp_path, "kern-1", 10_000, [b"X" * 100] * 300 + [b"THE-LAST-LINE"])
        assert read_log_tail(tmp_path / "kern-1.log", 10_000).endswith(b"THE-LAST-LINE")


class TestRotation:
    def test_a_full_file_is_rolled_aside(self, tmp_path: Path) -> None:
        active = tmp_path / "k.log"
        sink = RotatingLog(active, 10_000)
        try:
            sink.write(b"A" * 2_000)  # exactly max-size
            sink.write(b"B")  # ...so this one rolls it
        finally:
            sink.close()

        assert rotated_path(active, 1).read_bytes() == b"A" * 2_000
        assert active.read_bytes() == b"B"

    def test_the_oldest_is_deleted_once_the_set_is_full(self, tmp_path: Path) -> None:
        # A size cap on a log means the oldest output is deleted. That is not a compromise we are
        # introducing: `docker logs` cannot show it either.
        active = tmp_path / "k.log"
        sink = RotatingLog(active, 10_000)
        try:
            sink.write(b"X" * (2_000 * LOG_FILE_COUNT * 2))  # twice the whole budget
        finally:
            sink.close()

        present = [p for p in rotated_paths(active) if p.exists()]
        assert len(present) == LOG_FILE_COUNT  # the set never grows past max-file
        assert not rotated_path(active, LOG_FILE_COUNT).exists()


class TestReadingBackAcrossTheSet:
    def test_it_reads_oldest_to_newest(self, tmp_path: Path) -> None:
        active = tmp_path / "k.log"
        rotated_path(active, 2).write_bytes(b"one ")
        rotated_path(active, 1).write_bytes(b"two ")
        active.write_bytes(b"three")

        assert read_log_tail(active, 1000) == b"one two three"

    def test_reading_only_the_active_file_would_not_do(self, tmp_path: Path) -> None:
        # Right after a rotation the active file is nearly empty; the log the user wants is in the
        # rotated files. This is why get_logs reads across the set.
        active = tmp_path / "k.log"
        sink = RotatingLog(active, 10_000)
        try:
            sink.write(b"A" * 2_000)
            sink.write(b"B")
        finally:
            sink.close()

        assert read_log_tail(active, 10_000) == b"A" * 2_000 + b"B"

    def test_a_log_that_does_not_exist_reads_empty(self, tmp_path: Path) -> None:
        assert read_log_tail(tmp_path / "gone.log", 1000) == b""


class TestCleanup:
    def test_the_whole_set_is_removed(self, tmp_path: Path) -> None:
        # The rotated files are as much this kernel's log as the active one; leaving them behind
        # would leak the very disk this rotation exists to protect.
        active = tmp_path / "k.log"
        active.write_bytes(b"x")
        for i in range(1, LOG_FILE_COUNT):
            rotated_path(active, i).write_bytes(b"x")

        unlink_log_files(active)

        assert not any(p.exists() for p in rotated_paths(active))


class TestTheLauncher:
    def test_it_runs_the_writer_by_path_not_as_a_module(self, tmp_path: Path) -> None:
        # Running `-m ai.backend.agent.containerd.log_writer` would execute the package __init__,
        # which imports the whole agent — putting a second copy of the agent behind every container
        # and turning any import error in it into a container that cannot start.
        launcher = write_logger_launcher(tmp_path / "writer")
        script = launcher.read_text()

        assert script.startswith("#!/bin/sh")
        assert Path(log_writer.__file__).resolve().name in script
        assert " -m " not in script
        assert os.access(launcher, os.X_OK)

    def test_the_uri_carries_the_budget_containerd_flattens_into_argv(self, tmp_path: Path) -> None:
        uri = logger_uri(tmp_path / "writer", tmp_path / "logs", 10_000)
        assert uri.startswith("binary://")
        assert "--max-length=10000" in uri
        assert f"--log-root={tmp_path / 'logs'}".replace("/", "%2F") in uri
