"""What a scenario run says about itself, and the shapes a report comes out in.

A run writes one record per scenario as it goes; a reader groups the records by the
component and behaviour their module names carry, and renders the grouping. The record
crosses a process boundary as JSON, and this module is the only place that touches that
encoding.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, override

MARKS = {"passed": "pass", "failed": "FAIL", "skipped": "skip"}


@dataclass(frozen=True)
class Line:
    """레포트 한 줄. 자기가 어느 묶음 안에 있는지 안다."""

    says: str
    nest: tuple[str, ...] = ()
    """바깥부터 안쪽 순서. 묶음 없이 놓인 줄은 비어 있다."""


@dataclass(frozen=True)
class ScenarioRecord:
    """One scenario, as the run leaves it behind.

    The scenario fills what it says about itself; the run fills where it lived, how it
    came out, what it laid, and what the adapter it called offers.
    """

    summary: str
    description: str
    actor: str
    caller: str
    operation: str
    when: str
    then: str
    shows: tuple[str, ...] = ()
    """The arguments the call was made with, one each."""
    config: tuple[str, ...] = ()
    module: str = ""
    outcome: str = ""
    adapter: str = ""
    given: tuple[Line, ...] = ()
    seen: tuple[Line, ...] = ()
    """`then`이 자리마다 무엇을 보았는지."""
    offers: tuple[str, ...] = ()

    @property
    def component(self) -> str:
        """The component this scenario belongs to, read off its package path."""
        parts = self.module.split(".")
        return parts[-2] if len(parts) >= 2 else self.module

    @property
    def behaviour(self) -> str:
        """The behaviour it covers, read off its file name."""
        return self.module.split(".")[-1].removeprefix("test_")

    @property
    def failed(self) -> bool:
        return self.outcome == "failed"

    @property
    def mark(self) -> str:
        return MARKS.get(self.outcome, self.outcome)

    def situation(self) -> tuple[Line, ...]:
        """What was already true when the call was made: the rows, then the config."""
        return self.given + tuple(Line(says=one) for one in self.config)

    def as_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_line(cls, line: str) -> ScenarioRecord:
        raw: dict[str, Any] = json.loads(line)
        fields = {f: raw[f] for f in cls.__dataclass_fields__ if f in raw}
        for name in ("config", "offers", "shows"):
            if name in fields:
                fields[name] = tuple(fields[name])
        for name in ("given", "seen"):
            if name in fields:
                fields[name] = tuple(
                    Line(says=one["says"], nest=tuple(one["nest"])) for one in fields[name]
                )
        return cls(**fields)


@dataclass(frozen=True)
class BehaviourReport:
    """Every scenario one test module holds."""

    behaviour: str
    rows: tuple[ScenarioRecord, ...]


@dataclass(frozen=True)
class ComponentReport:
    """Every behaviour one component covers, and the calls it leaves alone."""

    component: str
    adapter: str
    behaviours: tuple[BehaviourReport, ...]
    unexercised: tuple[str, ...]

    @property
    def rows(self) -> tuple[ScenarioRecord, ...]:
        return tuple(row for behaviour in self.behaviours for row in behaviour.rows)

    @property
    def failing(self) -> int:
        return sum(1 for row in self.rows if row.failed)


@dataclass(frozen=True)
class Report:
    """What a run covers, by component."""

    components: tuple[ComponentReport, ...] = field(default_factory=tuple)

    @property
    def rows(self) -> tuple[ScenarioRecord, ...]:
        return tuple(row for component in self.components for row in component.rows)

    @property
    def failing(self) -> int:
        return sum(component.failing for component in self.components)

    @classmethod
    def of(cls, records: Iterable[ScenarioRecord]) -> Report:
        grouped: dict[str, dict[str, list[ScenarioRecord]]] = {}
        for record in records:
            grouped.setdefault(record.component, {}).setdefault(record.behaviour, []).append(record)
        return cls(
            tuple(
                ComponentReport(
                    component=component,
                    adapter=_adapter_of(behaviours),
                    behaviours=tuple(
                        BehaviourReport(
                            behaviour,
                            tuple(sorted(behaviours[behaviour], key=lambda r: r.summary)),
                        )
                        for behaviour in sorted(behaviours)
                    ),
                    unexercised=_unexercised(row for rows in behaviours.values() for row in rows),
                )
                for component, behaviours in sorted(grouped.items())
            )
        )


def _adapter_of(behaviours: dict[str, list[ScenarioRecord]]) -> str:
    for rows in behaviours.values():
        for row in rows:
            if row.adapter:
                return row.adapter
    return ""


def _unexercised(records: Iterable[ScenarioRecord]) -> tuple[str, ...]:
    """Adapter calls the run never made.

    What the adapter offers is read off the class, so this is the gap between the
    component's surface and the table, not between the table and a hand-kept list.
    """
    offered: set[str] = set()
    called: set[str] = set()
    for record in records:
        offered.update(record.offers)
        called.add(record.operation)
    return tuple(sorted(offered - called))


def records_of(lines: Iterable[str]) -> list[ScenarioRecord]:
    """Every record a run wrote, with the retried attempts of a scenario collapsed."""
    seen: dict[tuple[str, str], ScenarioRecord] = {}
    for line in lines:
        if not line.strip():
            continue
        record = ScenarioRecord.from_line(line)
        seen[(record.module, record.summary)] = record
    return list(seen.values())


class ReportFormat(ABC):
    """One way of writing a report out."""

    @abstractmethod
    def suffix(self) -> str:
        """The file extension a split report uses."""
        raise NotImplementedError

    @abstractmethod
    def render(self, report: Report) -> str:
        raise NotImplementedError

    @abstractmethod
    def render_one(self, component: ComponentReport) -> str:
        """One component alone, for a file that lives beside that component."""
        raise NotImplementedError


class MarkdownFormat(ReportFormat):
    """The document a person reads, and a release pull request carries."""

    @override
    def suffix(self) -> str:
        return "md"

    @override
    def render_one(self, component: ComponentReport) -> str:
        return "\n".join(self._component(component))

    @override
    def render(self, report: Report) -> str:
        out = ["# Scenario coverage", ""]
        out.append(
            f"{len(report.rows)} scenarios over {len(report.components)} components, "
            f"{report.failing} failing."
        )
        out.append("")
        out.append("| component | scenarios | behaviours | failing |")
        out.append("|---|---:|---|---:|")
        for component in report.components:
            names = ", ".join(b.behaviour for b in component.behaviours)
            out.append(
                f"| {component.component} | {len(component.rows)} | {names} | {component.failing} |"
            )
        out.append("")
        for component in report.components:
            out.extend(self._component(component))
        return "\n".join(out)

    def _component(self, component: ComponentReport) -> list[str]:
        out = [f"## {component.component}", ""]
        if component.unexercised:
            out.append(f"Not exercised by any scenario: {', '.join(component.unexercised)}.")
            out.append("")
        for behaviour in component.behaviours:
            out.append(f"### {behaviour.behaviour}")
            out.append("")
            for row in behaviour.rows:
                out.extend(self._row(row))
        return out

    def _row(self, row: ScenarioRecord) -> list[str]:
        out = [f"#### {row.summary} — {row.mark}", "", row.description, "", "Given", ""]
        out.extend(self._situation(row))
        out.extend(["", "When", "", f"- {row.when}"])
        out.extend(f"  - {one}" for one in row.shows)
        out.extend(["", "Then", "", f"- {row.then}"])
        out.extend(self._nested(row.seen, depth=1))
        out.append("")
        return out

    def _nested(self, lines: Sequence[Line], depth: int = 0) -> list[str]:
        """줄들을 자기 묶음 아래로 들여쓴다."""
        out: list[str] = []
        open_nests: tuple[str, ...] = ()
        for line in lines:
            shared = 0
            while (
                shared < len(open_nests)
                and shared < len(line.nest)
                and open_nests[shared] == line.nest[shared]
            ):
                shared += 1
            for at in range(shared, len(line.nest)):
                out.append(f"{'  ' * (depth + at)}- {line.nest[at]}")
            out.append(f"{'  ' * (depth + len(line.nest))}- {line.says}")
            open_nests = line.nest
        return out

    def _situation(self, row: ScenarioRecord) -> list[str]:
        """The rows, indented under the setup that laid them."""
        return self._nested(row.situation())


class JsonFormat(ReportFormat):
    """The same report for a tool to read."""

    @override
    def suffix(self) -> str:
        return "json"

    @override
    def render_one(self, component: ComponentReport) -> str:
        return json.dumps(asdict(component), indent=2, ensure_ascii=False)

    @override
    def render(self, report: Report) -> str:
        return json.dumps(
            {
                "scenarios": len(report.rows),
                "failing": report.failing,
                "components": [asdict(component) for component in report.components],
            },
            indent=2,
            ensure_ascii=False,
        )


class SummaryFormat(ReportFormat):
    """The counts alone, for a line in a build log."""

    @override
    def suffix(self) -> str:
        return "txt"

    @override
    def render_one(self, component: ComponentReport) -> str:
        return (
            f"{component.component}: {len(component.rows)} scenarios, "
            f"{component.failing} failing, {len(component.unexercised)} calls unexercised"
        )

    @override
    def render(self, report: Report) -> str:
        out = [
            f"{len(report.rows)} scenarios over {len(report.components)} components, "
            f"{report.failing} failing."
        ]
        for component in report.components:
            gap = (
                f", {len(component.unexercised)} calls unexercised" if component.unexercised else ""
            )
            out.append(
                f"  {component.component}: {len(component.rows)} scenarios, "
                f"{component.failing} failing{gap}"
            )
        return "\n".join(out)
