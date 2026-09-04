"""Baseline, re-snapshot, diff — the assertion every data-plane scenario ends with.

Three decisions worth stating, because each of them is what makes the guard usable rather than
merely correct:

**Delta, not zero.** A developer host runs other agents, other sessions, and Docker. Asserting
"no `bai*` devices exist" would fail everywhere and be disabled within a day. The guard asserts
that the set of resources is the same as before the scenario ran.

**Poll, don't sample once.** Teardown is asynchronous end to end — a destroy returns before
containerd has reaped the shim and before the runner has removed the bridge. A single post-hoc
sample would be flaky in exactly the direction that trains people to add `sleep`. The guard polls
until the delta is empty, and reports the time it took, which is itself the number to watch: a
teardown that grew from 2s to 20s is a regression the "passed" result would otherwise hide.

**Report disappearances too.** A resource that was in the baseline and is gone afterwards means
the scenario destroyed something that was not its own — the cross-session bridge deletion the
shared `bailo{n}` name space makes possible. That is a worse bug than a leak, and silent under a
leak-only check.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Sequence
from dataclasses import dataclass, field

from ai.backend.testutils.dataplane.collectors.base import (
    Resource,
    ResourceCollector,
    group_by_kind,
)


@dataclass(frozen=True)
class LeakReport:
    leaked: tuple[Resource, ...]
    collateral: tuple[Resource, ...]
    elapsed: float = 0.0
    polls: int = 1

    @property
    def clean(self) -> bool:
        return not self.leaked and not self.collateral

    def format(self) -> str:
        sections: list[str] = []
        if self.leaked:
            sections.append(_format_group("LEAKED (survived teardown)", self.leaked))
        if self.collateral:
            sections.append(
                _format_group("COLLATERAL (existed before the test, now gone)", self.collateral)
            )
        sections.append(f"settled after {self.polls} poll(s) over {self.elapsed:.1f}s")
        return "\n".join(sections)


def _format_group(title: str, resources: Sequence[Resource]) -> str:
    lines = [f"{title}: {len(resources)}"]
    for kind, items in group_by_kind(resources).items():
        lines.append(f"  [{kind}] {len(items)}")
        lines.extend(f"    - {item}" for item in items)
    return "\n".join(lines)


@dataclass
class LeakGuard:
    """Holds a baseline and diffs against it.

    `ignore` exists for the resources a scenario legitimately creates and keeps — a warm image
    pull, a session it hands to the next test. Prefer moving that work *before* `baseline()` so
    it lands in the baseline naturally; an ignore list that grows is a guard losing its teeth.
    """

    collectors: Sequence[ResourceCollector]
    ignore: set[Resource] = field(default_factory=set)
    _baseline: frozenset[Resource] | None = field(default=None, init=False)
    quiesced: bool = field(default=False, init=False)
    """Whether the baseline was taken on a host that had stopped changing. False means the
    baseline is the intersection of two still-differing samples — usable, but a scenario running
    against a busy host should say so when it reports."""

    async def snapshot(self) -> frozenset[Resource]:
        # Collect concurrently: a two-node run with six collectors each is a dozen ssh round-trips,
        # and doing them in series makes the poll interval — and so the reported settle time —
        # meaningless.
        results = await asyncio.gather(*(c.collect() for c in self.collectors))
        found: set[Resource] = set()
        for result in results:
            found |= result
        return frozenset(found - self.ignore)

    async def stable_snapshot(
        self, *, max_wait: float = 10.0, interval: float = 0.5
    ) -> tuple[frozenset[Resource], bool]:
        """Sample until two consecutive snapshots agree. Returns ``(snapshot, quiesced)``.

        Shared by `baseline` and by any scenario that needs a trustworthy mid-test picture — a
        restart scenario comparing before against after needs both sides taken this way, or the
        comparison reports the settling as a change.
        """
        started = time.monotonic()
        previous = await self.snapshot()
        while True:
            current = await self.snapshot()
            if current == previous:
                return current, True
            if time.monotonic() - started >= max_wait:
                return previous & current, False
            previous = current
            await asyncio.sleep(interval)

    async def baseline(
        self, *, max_wait: float = 10.0, interval: float = 0.5
    ) -> frozenset[Resource]:
        """Sample until two consecutive snapshots agree, and take that as the baseline.

        A single sample can catch a *phantom*: no collector sees the host atomically, so an object
        created between two of its listings shows up half-formed — a containerd task whose
        container record did not exist yet when `containers list` ran. The production code states
        the same hazard and answers it by taking both views from one listing
        (`_live_and_own_containers`); nothing here can do that across `ctr` invocations, so the
        answer is to require the picture to repeat before trusting it.

        Getting this wrong is worse than it sounds: a phantom in the baseline that resolves during
        the test is reported as COLLATERAL — "the scenario destroyed something that was not its
        own" — which is the suite's loudest failure, raised for nothing.

        On a host that never settles (another session is being created throughout), the baseline
        falls back to the intersection of the last two samples — everything seen twice — and
        `quiesced` is left False.
        """
        snapshot, quiesced = await self.stable_snapshot(max_wait=max_wait, interval=interval)
        self._baseline = snapshot
        self.quiesced = quiesced
        return snapshot

    def _diff(self, current: frozenset[Resource]) -> tuple[tuple[Resource, ...], ...]:
        if self._baseline is None:
            raise RuntimeError("LeakGuard.baseline() was never called")
        return (
            tuple(sorted(current - self._baseline)),
            tuple(sorted(self._baseline - current)),
        )

    async def settle(self, *, max_wait: float = 60.0, interval: float = 1.0) -> LeakReport:
        """Poll until the delta is empty, or until `max_wait` seconds have passed.

        Returns the last report either way — the caller decides whether a non-empty delta is a
        failure, because a few scenarios (a deliberately killed agent, an adopt test) assert on
        the *contents* of the delta rather than on its emptiness.
        """
        started = time.monotonic()
        polls = 0
        leaked: tuple[Resource, ...] = ()
        collateral: tuple[Resource, ...] = ()
        while True:
            polls += 1
            leaked, collateral = self._diff(await self.snapshot())
            elapsed = time.monotonic() - started
            if not leaked and not collateral:
                return LeakReport((), (), elapsed, polls)
            if elapsed >= max_wait:
                return LeakReport(leaked, collateral, elapsed, polls)
            await asyncio.sleep(interval)

    async def assert_clean(self, *, max_wait: float = 60.0, interval: float = 1.0) -> LeakReport:
        report = await self.settle(max_wait=max_wait, interval=interval)
        if not report.clean:
            raise AssertionError("host state did not return to baseline\n" + report.format())
        return report


def compare(before: frozenset[Resource], after: frozenset[Resource]) -> LeakReport:
    """Diff two snapshots taken by the same guard.

    For scenarios that assert on a *transition* rather than on a return to baseline — "the agent
    restarted and the host is byte-for-byte where it was". The vocabulary is deliberately the
    guard's own: ``leaked`` is what appeared, ``collateral`` is what vanished, so a restart that
    destroyed a live session's bridge reads the same way it would at teardown.
    """
    return LeakReport(
        leaked=tuple(sorted(after - before)),
        collateral=tuple(sorted(before - after)),
    )
