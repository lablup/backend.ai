"""The unit a leak is expressed in.

A resource is identified by ``(kind, node, ident)`` and nothing else. ``detail`` carries the
volatile text a human needs to act on the report — a task's status, a rule's table, a link's
master — and is deliberately kept out of the identity, so a container that merely changed state
between two snapshots is not reported as one resource vanishing and another appearing.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Protocol, override


@dataclass(frozen=True, order=True)
class Resource:
    kind: str
    node: str
    ident: str
    detail: str = field(default="", compare=False)

    @override
    def __str__(self) -> str:
        location = f"@{self.node}" if self.node else ""
        suffix = f"  ({self.detail})" if self.detail else ""
        return f"{self.kind}{location}: {self.ident}{suffix}"


class ResourceCollector(Protocol):
    """One question asked of one host.

    `collect` MUST raise when it cannot answer. Returning an empty set on failure would make the
    host look clean, which is the only way this harness can produce a false negative.
    """

    @property
    def kind(self) -> str: ...

    async def collect(self) -> set[Resource]: ...


def group_by_kind(resources: Iterable[Resource]) -> dict[str, list[Resource]]:
    grouped: dict[str, list[Resource]] = {}
    for resource in sorted(resources):
        grouped.setdefault(resource.kind, []).append(resource)
    return grouped
