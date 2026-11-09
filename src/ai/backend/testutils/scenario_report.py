"""What a scenario run says about itself, and the shapes a report comes out in.

A run writes one record per scenario as it goes; a reader groups the records by the
component and behaviour their module names carry, and renders the grouping. The record
crosses a process boundary as JSON, and this module is the only place that touches that
encoding.
"""

from __future__ import annotations

import ast
import enum
import json
import pathlib
import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar, override

from ai.backend.testutils.scenario_steps import Language, Refused, Says

MARKS = {"passed": "pass", "failed": "FAIL", "skipped": "skip"}
HANGUL = re.compile("[ᄀ-ᇿ㄰-㆏가-힣]")
PARTICLE = re.compile(
    r"([A-Za-z])(입니다|이며|이고|이란|이라는|에서는|에게는|으로는|으로|에서|에게|"
    r"부터|까지|에는|에도|이|가|은|는|을|를|와|과|로|만|도|의|에|인|나|며|라)"
)


class OperationWords:
    """The words the report says; translating the report is editing these."""

    GAP_MARK: ClassVar[str] = "SCENARIO-GAP"
    """붙은 연산은 기본 시나리오 행이 모자라다. 이 말로 검색한다."""
    STATUS: ClassVar[Says] = Says("시나리오", english="Scenario")
    COMPLETE: ClassVar[Says] = Says("완성", english="complete")
    INCOMPLETE: ClassVar[Says] = Says("미완성", english="incomplete")
    REPRESENTATIVE_SUCCESS: ClassVar[Says] = Says("대표 성공", english="representative success")
    REPRESENTATIVE_REFUSAL: ClassVar[Says] = Says("대표 거부", english="representative rejection")
    SUCCESS: ClassVar[Says] = Says("성공", english="success")
    REFUSAL: ClassVar[Says] = Says("거부", english="rejection")
    SCENARIO: ClassVar[Says] = Says("시나리오", english="scenario")
    VERDICT: ClassVar[Says] = Says("판정", english="verdict")
    ANSWERED: ClassVar[Says] = Says("성공", english="answered")
    REFUSED: ClassVar[Says] = Says("거부", english="rejected")
    PRESENT: ClassVar[Says] = Says("있음", english="present")
    ABSENT: ClassVar[Says] = Says("없음", english="absent")
    BACKGROUND: ClassVar[Says] = Says("배경", english="background")
    ADAPTER: ClassVar[Says] = Says("어댑터", english="adapter")
    COVERED: ClassVar[str] = "✓"
    MISSING: ClassVar[str] = "✗"


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

    def source(self) -> str:
        """이 행이 사는 파일. 레포트가 거기로 걸어준다."""
        return "/tests/scenario/" + self.module.replace(".", "/") + ".py"

    def anchor(self) -> str:
        """Where the report links to this row's details; a summary can repeat across modules."""
        return f"{self.behaviour}-{self.summary}"

    def called(self) -> str:
        """어느 엔티티의 어느 호출인지. 이름만으로는 잘 안 보인다."""
        return f"{self.adapter}.{self.operation}" if self.adapter else self.operation

    @property
    def mark(self) -> str:
        return MARKS.get(self.outcome, self.outcome)

    def situation(self) -> tuple[Line, ...]:
        """What was already true when the call was made: the rows, then the config."""
        return self.given + tuple(Line(says=one) for one in self.config)

    def expects_refusal(self) -> bool:
        """Whether `then` expected the call to be refused."""
        return any(line.says.startswith(Refused.PREFIX) for line in self.seen)

    def as_line(self) -> str:
        return json.dumps(_jsonable(asdict(self)), ensure_ascii=False)

    @classmethod
    def from_line(cls, line: str) -> ScenarioRecord:
        raw: dict[str, Any] = json.loads(line)
        fields = {f: raw[f] for f in cls.__dataclass_fields__ if f in raw}
        for name in ("description", "when", "then"):
            if name in fields:
                fields[name] = Says.from_data(fields[name])
        for name in ("offers", "shows"):
            if name in fields:
                fields[name] = tuple(fields[name])
        if "config" in fields:
            fields["config"] = tuple(Says.from_data(one) for one in fields["config"])
        for name in ("given", "seen"):
            if name in fields:
                fields[name] = tuple(
                    Line(
                        says=Says.from_data(one["says"]),
                        nest=tuple(Says.from_data(nest) for nest in one["nest"]),
                    )
                    for one in fields[name]
                )
        return cls(**fields)


@dataclass(frozen=True)
class BehaviourReport:
    """Every scenario one test module holds."""

    behaviour: str
    rows: tuple[ScenarioRecord, ...]


class Composition(enum.StrEnum):
    """How an adapter operation is built, in the order a report lists them."""

    OPS = "ops 구성"
    MIXED = "ops + 직접 구현"
    CUSTOM = "직접 구현"
    NO_ACTION = "Action 없음"

    def in_(self, language: Language) -> str:
        """The label this composition gets in a report."""
        if language is Language.KOREAN:
            return self.value
        return {
            Composition.OPS: "built from ops",
            Composition.MIXED: "ops + direct implementation",
            Composition.CUSTOM: "direct implementation",
            Composition.NO_ACTION: "no Action",
        }[self]


@dataclass(frozen=True)
class OperationReport:
    """One adapter operation: the group methods that build it and the rows calling it."""

    operation: str
    composition: Composition
    group_methods: tuple[str, ...]
    succeeding: int
    refused: int

    @property
    def complete(self) -> bool:
        """A success row and a refusal row; an operation with no action has no gate to refuse."""
        if self.composition is Composition.NO_ACTION:
            return bool(self.succeeding)
        return bool(self.succeeding and self.refused)


@dataclass(frozen=True)
class ComponentReport:
    """Every behaviour one component covers, and how each operation of its adapter is built."""

    component: str
    adapter: str
    behaviours: tuple[BehaviourReport, ...]
    operations: tuple[OperationReport, ...]
    knowledge_doc: str = ""
    """The component's KNOWLEDGE.md, empty when the component has none."""

    @property
    def gaps(self) -> tuple[str, ...]:
        return tuple(one.operation for one in self.operations if not one.complete)

    def knowledge(self) -> str:
        """Where the component's background is written."""
        return self.knowledge_doc

    def adapter_source(self) -> str:
        return f"/src/ai/backend/manager/api/adapters/{self.component}/adapter.py"

    @property
    def rows(self) -> tuple[ScenarioRecord, ...]:
        return tuple(row for behaviour in self.behaviours for row in behaviour.rows)

    @property
    def adapters(self) -> tuple[str, ...]:
        return tuple(sorted({row.adapter for row in self.rows if row.adapter}))

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
    def of(cls, records: Iterable[ScenarioRecord], wiring: AdapterWiring) -> Report:
        grouped: dict[str, dict[str, list[ScenarioRecord]]] = {}
        for record in records:
            grouped.setdefault(record.component, {}).setdefault(record.behaviour, []).append(record)
        components = []
        for component, behaviours in sorted(grouped.items()):
            rows = [row for rows in behaviours.values() for row in rows]
            components.append(
                ComponentReport(
                    component=component,
                    adapter=_adapter_of(rows),
                    behaviours=tuple(
                        BehaviourReport(
                            behaviour,
                            tuple(sorted(behaviours[behaviour], key=lambda r: r.summary)),
                        )
                        for behaviour in sorted(behaviours)
                    ),
                    operations=_operations(component, rows, wiring),
                    knowledge_doc=wiring.knowledge_doc(component),
                )
            )
        return cls(tuple(components))


def _adapter_of(rows: Sequence[ScenarioRecord]) -> str:
    """The adapter most rows call, so the answer does not hang on the order records arrive in."""
    counts: dict[str, int] = {}
    for row in rows:
        if row.adapter:
            counts[row.adapter] = counts.get(row.adapter, 0) + 1
    return min(counts, key=lambda adapter: (-counts[adapter], adapter), default="")


def _operations(
    component: str, records: Sequence[ScenarioRecord], wiring: AdapterWiring
) -> tuple[OperationReport, ...]:
    """Every operation each adapter the rows call defines, with the rows that called it.

    A ``BaseAdapter`` method is final to every adapter, so it is no adapter's operation.
    A component calling several adapters names each operation with its adapter.
    """
    adapters = sorted({record.adapter for record in records if record.adapter})
    out = []
    for adapter in adapters:
        for operation, built in sorted(wiring.of(component, adapter).items()):
            calls = [
                record
                for record in records
                if record.adapter == adapter and record.operation == operation
            ]
            refused = sum(1 for record in calls if record.expects_refusal())
            out.append(
                OperationReport(
                    operation=operation if len(adapters) == 1 else f"{adapter}.{operation}",
                    composition=built.composition,
                    group_methods=built.group_methods,
                    succeeding=len(calls) - refused,
                    refused=refused,
                )
            )
    return tuple(out)


@dataclass(frozen=True)
class OperationWiring:
    """The group methods that built the processors one adapter operation runs."""

    composition: Composition
    group_methods: tuple[str, ...]


@dataclass
class _ProcessorsClass:
    group_methods: dict[str, str] = field(default_factory=dict)
    """Field → the group method, or the constructor, that built it."""
    nested: dict[str, str] = field(default_factory=dict)
    """Field → the ``*Processors`` class it holds."""


class AdapterWiring:
    """Follows adapter method → processor field → group method through the source.

    A processor built by a ``*lookup*`` method only resolves a key for the one that
    follows, so it decides the composition only when nothing else is run.
    """

    _manager: pathlib.Path
    _processors: dict[str, _ProcessorsClass] | None

    def __init__(self, manager: pathlib.Path) -> None:
        self._manager = manager
        self._processors = None

    def knowledge_doc(self, component: str) -> str:
        """The component's KNOWLEDGE.md, or empty when it has none."""
        path = self._manager / "api" / "adapters" / component / "KNOWLEDGE.md"
        if not path.is_file():
            return ""
        return f"/src/ai/backend/manager/api/adapters/{component}/KNOWLEDGE.md"

    def of(self, component: str, adapter: str) -> Mapping[str, OperationWiring]:
        """Every public operation the adapter class defines itself."""
        cls = self._adapter_class(component, adapter)
        if cls is None:
            raise LookupError(f"No adapter class {adapter!r} under api/adapters/{component}")
        methods = {
            node.name: node
            for node in cls.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        dependencies = self._dependencies(cls, methods.get("__init__"))
        return {
            name: self._wiring(self._reached(name, methods, dependencies))
            for name, method in methods.items()
            if isinstance(method, ast.AsyncFunctionDef) and not name.startswith("_")
        }

    def _adapter_class(self, component: str, adapter: str) -> ast.ClassDef | None:
        adapters = self._manager / "api" / "adapters"
        for candidates in (
            sorted((adapters / component).glob("*.py")),
            sorted(adapters.rglob("*.py")),
        ):
            for path in candidates:
                for node in ast.parse(path.read_text(encoding="utf8")).body:
                    if isinstance(node, ast.ClassDef) and node.name == adapter:
                        return node
        return None

    def _dependencies(
        self, cls: ast.ClassDef, init: ast.FunctionDef | ast.AsyncFunctionDef | None
    ) -> dict[str, str]:
        """Attribute → the ``*Processors`` class the adapter was handed for it."""
        out = {
            node.target.id: self._class_name(node.annotation)
            for node in cls.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        }
        if init is not None:
            params = {
                arg.arg: self._class_name(arg.annotation)
                for arg in (*init.args.args, *init.args.kwonlyargs)
                if arg.annotation is not None
            }
            for node in ast.walk(init):
                if (
                    isinstance(node, ast.Assign)
                    and len(node.targets) == 1
                    and isinstance(target := node.targets[0], ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id in params
                ):
                    out[target.attr] = params[node.value.id]
        return {name: kind for name, kind in out.items() if kind.endswith("Processors")}

    def _reached(
        self,
        name: str,
        methods: Mapping[str, ast.FunctionDef | ast.AsyncFunctionDef],
        dependencies: Mapping[str, str],
    ) -> set[str]:
        """The group methods behind every processor the method and its helpers touch."""
        processors = self._processors_index()
        reached: set[str] = set()
        visited: set[str] = set()
        pending = [name]
        while pending:
            current = pending.pop()
            if current in visited or current not in methods:
                continue
            visited.add(current)
            for node in ast.walk(methods[current]):
                if not isinstance(node, ast.Attribute):
                    continue
                chain = self._self_chain(node)
                if len(chain) == 1:
                    pending.append(chain[0])
                    continue
                if len(chain) < 2 or chain[0] not in dependencies:
                    continue
                cls = processors.get(dependencies[chain[0]])
                for part in chain[1:]:
                    if cls is None:
                        break
                    if part in cls.group_methods:
                        reached.add(cls.group_methods[part])
                        break
                    cls = processors.get(cls.nested.get(part, ""))
        return reached

    def _wiring(self, group_methods: set[str]) -> OperationWiring:
        deciding = {method for method in group_methods if "lookup" not in method} or group_methods
        if not deciding:
            composition = Composition.NO_ACTION
        elif all(method.endswith("_ops") for method in deciding):
            composition = Composition.OPS
        elif any(method.endswith("_ops") for method in deciding):
            composition = Composition.MIXED
        else:
            composition = Composition.CUSTOM
        return OperationWiring(composition, tuple(sorted(deciding)))

    def _processors_index(self) -> dict[str, _ProcessorsClass]:
        if self._processors is None:
            services = self._manager / "services"
            paths = {*services.rglob("processors*.py"), *services.rglob("processors/*.py")}
            self._processors = {}
            for path in sorted(paths):
                for node in ast.walk(ast.parse(path.read_text(encoding="utf8"))):
                    if isinstance(node, ast.ClassDef) and node.name.endswith("Processors"):
                        found = self._processors.setdefault(node.name, _ProcessorsClass())
                        self._read_processors_class(node, found)
        return self._processors

    def _read_processors_class(self, cls: ast.ClassDef, into: _ProcessorsClass) -> None:
        for statement in cls.body:
            if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                kind = self._class_name(statement.annotation)
                if kind.endswith("Processors"):
                    into.nested[statement.target.id] = kind
        for node in ast.walk(cls):
            if not (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(target := node.targets[0], ast.Attribute)
                and isinstance(node.value, ast.Call)
            ):
                continue
            called = node.value.func
            name = called.attr if isinstance(called, ast.Attribute) else getattr(called, "id", "")
            if name.endswith("Processors"):
                into.nested[target.attr] = name
            elif name:
                into.group_methods[target.attr] = name

    def _class_name(self, annotation: ast.expr) -> str:
        """The class an annotation names, without its parameters or an ``| None``."""
        match annotation:
            case ast.Name(id=name):
                return name
            case ast.Attribute(attr=name):
                return name
            case ast.Subscript(value=value):
                return self._class_name(value)
            case ast.BinOp(left=left):
                return self._class_name(left)
            case ast.Constant(value=str(text)):
                return text.split("[")[0].split("|")[0].strip()
        return ""

    def _self_chain(self, node: ast.Attribute) -> list[str]:
        """``self.a.b.c`` as ``["a", "b", "c"]``; empty when it does not start at ``self``."""
        parts: list[str] = []
        current: ast.expr = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if not (isinstance(current, ast.Name) and current.id == "self"):
            return []
        return parts[::-1]


def _jsonable(value: Any) -> Any:
    """The JSON a run writes: a sentence carries both languages, a label its value."""
    match value:
        case Says():
            return value.as_data()
        case enum.Enum():
            return _jsonable(value.value)
        case Mapping():
            return {key: _jsonable(one) for key, one in value.items()}
        case list() | tuple():
            return [_jsonable(one) for one in value]
        case str():
            return str(value)
    return value


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
    def file_name(self) -> str:
        """The file a split report writes for one component."""
        raise NotImplementedError

    def variants(self) -> Mapping[str, ReportFormat]:
        """The files a split report writes, keyed by file name; a bilingual format has two."""
        return {self.file_name(): self}

    @abstractmethod
    def render(self, report: Report) -> str:
        raise NotImplementedError

    @abstractmethod
    def render_one(self, component: ComponentReport) -> str:
        """One component alone, for a file that lives beside that component."""
        raise NotImplementedError


class MarkdownFormat(ReportFormat):
    """The document a person reads, and a release pull request carries.

    Every sentence is written in both languages. A sentence whose English is not
    written yet falls back to the Korean one.
    """

    _language: Language

    def __init__(self, language: Language = Language.ENGLISH) -> None:
        self._language = language

    @override
    def file_name(self) -> str:
        return "report.md" if self._language is Language.ENGLISH else "report.ko.md"

    @override
    def variants(self) -> Mapping[str, ReportFormat]:
        return {
            one.file_name(): one
            for one in (MarkdownFormat(Language.ENGLISH), MarkdownFormat(Language.KOREAN))
        }

    def _spoken(self, text: str) -> str:
        return text.in_(self._language) if isinstance(text, Says) else text

    @override
    def render_one(self, component: ComponentReport) -> str:
        text = "\n".join(self._component(component))
        if self._language is Language.KOREAN:
            text = PARTICLE.sub(r"\1 \2", text)
        if self._language is Language.ENGLISH and HANGUL.search(text):
            lines = [line for line in text.splitlines() if HANGUL.search(line)]
            raise ValueError(
                f"{component.component}: the English report still says {len(lines)} Korean "
                f"line(s):\n" + "\n".join(lines)
            )
        return text

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
        words = OperationWords
        out = [f"## {component.component}", ""]
        links = []
        if doc := component.knowledge():
            links.append(f"[{self._spoken(words.BACKGROUND)}]({doc})")
        links.append(f"[{self._spoken(words.ADAPTER)}]({component.adapter_source()})")
        out.append(" · ".join(links))
        out.append("")
        if component.operations:
            out.append(self._status(component))
            out.append("")
            out.extend(self._operations(component.operations))
            out.append("")
        calls = self._calls(component)
        for operation, rows in calls:
            out.extend(self._table(operation, rows))
            out.append("")
        for operation, rows in calls:
            out.append(f"### {operation}")
            out.append("")
            for row in rows:
                out.extend(self._row(row))
        return out

    def _status(self, component: ComponentReport) -> str:
        words = OperationWords
        if not component.gaps:
            return f"{self._spoken(words.STATUS)}: {self._spoken(words.COMPLETE)}"
        return (
            f"{self._spoken(words.STATUS)}: {self._spoken(words.INCOMPLETE)}"
            f" {len(component.gaps)} / {len(component.operations)}"
        )

    def _operations(self, operations: Sequence[OperationReport]) -> list[str]:
        """Each operation once, under how it is built.

        An operation built only from ops needs one success and one refusal row; the
        shared combinations are the ops contract tests' to cover.
        """
        out: list[str] = []
        for composition in Composition:
            members = [one for one in operations if one.composition is composition]
            if not members:
                continue
            out.append(f"- {composition.in_(self._language)} ({len(members)})")
            for one in members:
                out.append(f"  - {self._operation(one)}")
        return out

    def _operation(self, one: OperationReport) -> str:
        words = OperationWords
        if one.composition is Composition.OPS:
            succeeding = words.COVERED if one.succeeding else words.MISSING
            refused = words.COVERED if one.refused else words.MISSING
            says = (
                f"{one.operation}: {self._spoken(words.REPRESENTATIVE_SUCCESS)} {succeeding}"
                f" · {self._spoken(words.REPRESENTATIVE_REFUSAL)} {refused}"
            )
        else:
            says = (
                f"{one.operation}: {self._spoken(words.SUCCESS)} {self._count(one.succeeding)}"
                f" · {self._spoken(words.REFUSAL)} {self._count(one.refused)}"
            )
            if one.group_methods:
                says += f" ({', '.join(one.group_methods)})"
        if not one.complete:
            says += f": {words.GAP_MARK}"
        return says

    def _count(self, rows: int) -> str:
        words = OperationWords
        return f"{self._spoken(words.PRESENT)} {rows}" if rows else self._spoken(words.ABSENT)

    def _calls(self, component: ComponentReport) -> list[tuple[str, list[ScenarioRecord]]]:
        """The rows by operation, in the order the list names them and then any it does not.

        Successes come before refusals, each in summary order.
        """
        several_adapters = len(component.adapters) > 1
        calls: dict[str, list[ScenarioRecord]] = {}
        for row in sorted(component.rows, key=lambda r: (r.expects_refusal(), r.summary)):
            name = row.called() if several_adapters else row.operation
            calls.setdefault(name, []).append(row)
        listed = [
            one.operation
            for composition in Composition
            for one in component.operations
            if one.composition is composition
        ]
        return [
            (operation, calls[operation])
            for operation in [*listed, *sorted(set(calls) - set(listed))]
            if operation in calls
        ]

    def _table(self, operation: str, rows: Sequence[ScenarioRecord]) -> list[str]:
        """One line per row, linking to its details below."""
        words = OperationWords
        header = f"| {self._spoken(words.SCENARIO)} | {self._spoken(words.VERDICT)} |"
        out = [f"**{operation}**", "", header, "|---|---|"]
        for row in rows:
            verdict = words.REFUSED if row.expects_refusal() else words.ANSWERED
            description = self._spoken(row.description).replace("|", "\\|")
            out.append(f"| [{description}](#{row.anchor()}) | {self._spoken(verdict)} |")
        return out

    def _row(self, row: ScenarioRecord) -> list[str]:
        out = [
            f'<a id="{row.anchor()}"></a>',
            "",
            f"#### [{row.summary}]({row.source()}): {row.mark}",
            "",
            self._spoken(row.description),
            "",
            "Given",
            "",
        ]
        out.extend(self._situation(row))
        out.extend(["", "When", "", f"- {row.called()}: {self._spoken(row.when)}"])
        out.extend(f"  - {one}" for one in row.shows)
        out.extend(["", "Then", "", f"- {self._spoken(row.then)}"])
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
                out.append(f"{'  ' * (depth + at)}- {self._spoken(line.nest[at])}")
            out.append(f"{'  ' * (depth + len(line.nest))}- {self._spoken(line.says)}")
            open_nests = line.nest
        return out

    def _situation(self, row: ScenarioRecord) -> list[str]:
        """The rows, indented under the setup that laid them."""
        return self._nested(row.situation())


class JsonFormat(ReportFormat):
    """The same report for a tool to read, with every sentence in both languages."""

    @override
    def file_name(self) -> str:
        return "report.json"

    @override
    def render_one(self, component: ComponentReport) -> str:
        return json.dumps(_jsonable(asdict(component)), indent=2, ensure_ascii=False)

    @override
    def render(self, report: Report) -> str:
        return json.dumps(
            _jsonable({
                "scenarios": len(report.rows),
                "failing": report.failing,
                "components": [asdict(component) for component in report.components],
            }),
            indent=2,
            ensure_ascii=False,
        )


class SummaryFormat(ReportFormat):
    """The counts alone, for a line in a build log."""

    @override
    def file_name(self) -> str:
        return "report.txt"

    @override
    def render_one(self, component: ComponentReport) -> str:
        return (
            f"{component.component}: {len(component.rows)} scenarios, "
            f"{component.failing} failing, {len(component.gaps)} {OperationWords.GAP_MARK}"
        )

    @override
    def render(self, report: Report) -> str:
        out = [
            f"{len(report.rows)} scenarios over {len(report.components)} components, "
            f"{report.failing} failing."
        ]
        for component in report.components:
            gap = f", {len(component.gaps)} {OperationWords.GAP_MARK}" if component.gaps else ""
            out.append(
                f"  {component.component}: {len(component.rows)} scenarios, "
                f"{component.failing} failing{gap}"
            )
        return "\n".join(out)
