"""Per-process counters that must not grow, for soak scenarios.

These are gauges, not resources: they are never "leaked", they *drift*. A churn loop that creates
and destroys a thousand sessions can leave every set-valued collector clean and still have raised
the agent's descriptor count by a thousand — the netns and pidfd pins the attach path opens are
exactly the kind of fd that goes unnoticed until a long-running agent hits its rlimit.

Compare a gauge against a baseline with `assert_no_drift`, never against an absolute value: the
agent's steady-state fd count is a function of the site's configuration, not something a test can
know.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.testutils.dataplane.nodes import CommandFailed, Node


@dataclass(frozen=True)
class ProcessGauge:
    node: str
    pid: int
    command: str
    fds: int
    threads: int
    rss_kib: int

    @override
    def __str__(self) -> str:
        return (
            f"{self.command}[{self.pid}]@{self.node}: "
            f"fds={self.fds} threads={self.threads} rss={self.rss_kib}KiB"
        )


class ProcessGaugeCollector:
    """Gauges for every process on a node matching a pgrep pattern."""

    _node: Node
    _pattern: str

    def __init__(self, node: Node, *, pattern: str) -> None:
        self._node = node
        self._pattern = pattern

    @property
    def kind(self) -> str:
        return "process-gauge"

    def parse(self, raw: str) -> dict[int, ProcessGauge]:
        gauges: dict[int, ProcessGauge] = {}
        for line in raw.splitlines():
            if not line.strip():
                continue
            fields = line.split("\t")
            if len(fields) != 5:
                raise CommandFailed(f"[{self._node.name}] unexpected gauge line: {line!r}")
            pid_s, command, fds_s, threads_s, rss_s = fields
            if "pgrep" in command:
                # `pgrep -f` excludes itself but not the `sh -c` (and `sudo`) whose command line
                # *contains* the pattern, so the query matches processes of our own making. Their
                # PIDs differ on every poll, so leaving them in would churn the gauge set and hide
                # the drift the caller is actually watching for.
                continue
            gauges[int(pid_s)] = ProcessGauge(
                node=self._node.name,
                pid=int(pid_s),
                command=command,
                fds=int(fds_s),
                threads=int(threads_s),
                rss_kib=int(rss_s or 0),
            )
        return gauges

    async def collect(self) -> dict[int, ProcessGauge]:
        # One shell round-trip for all matches: over ssh, a per-pid round-trip would take longer
        # than the churn interval a soak test is trying to measure. The shell only gathers; which
        # rows count is decided in `parse`, where it can be tested.
        #
        # `tr` folds newlines as well as NULs: a command line can legitimately contain a newline
        # (any `sh -c` with a multi-line script does), and one row spilling onto two lines breaks
        # the field count for every reader.
        script = (
            f"pgrep -f {self._pattern!r} | while read -r p; do "
            '[ -d "/proc/$p" ] || continue; '
            'cmd=$(tr "\\0\\n" "  " < "/proc/$p/cmdline" | cut -c1-60); '
            'fds=$(ls "/proc/$p/fd" 2>/dev/null | wc -l); '
            'th=$(awk "/^Threads:/ {print \\$2}" "/proc/$p/status"); '
            'rss=$(awk "/^VmRSS:/ {print \\$2}" "/proc/$p/status"); '
            'printf "%s\\t%s\\t%s\\t%s\\t%s\\n" "$p" "$cmd" "$fds" "$th" "$rss"; '
            "done"
        )
        result = await self._node.run(["sh", "-c", script])
        return self.parse(result.stdout)


def assert_no_drift(
    before: dict[int, ProcessGauge],
    after: dict[int, ProcessGauge],
    *,
    max_fd_growth: int = 8,
    max_thread_growth: int = 4,
    max_rss_growth_kib: int = 128 * 1024,
) -> None:
    """Fail when a surviving process grew past the allowances.

    Only PIDs present in both snapshots are compared. A process that restarted mid-run has no
    meaningful "growth" — and a scenario that restarts the agent on purpose would otherwise get a
    guaranteed failure here.
    """
    problems: list[str] = []
    for pid, old in before.items():
        new = after.get(pid)
        if new is None:
            continue
        if new.fds - old.fds > max_fd_growth:
            problems.append(f"{new}: fds {old.fds} -> {new.fds} (allowed +{max_fd_growth})")
        if new.threads - old.threads > max_thread_growth:
            problems.append(
                f"{new}: threads {old.threads} -> {new.threads} (allowed +{max_thread_growth})"
            )
        if new.rss_kib - old.rss_kib > max_rss_growth_kib:
            problems.append(
                f"{new}: rss {old.rss_kib} -> {new.rss_kib} KiB (allowed +{max_rss_growth_kib} KiB)"
            )
    if problems:
        raise AssertionError("process gauges drifted:\n  " + "\n  ".join(problems))
