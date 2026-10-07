from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SeedItemFailure:
    """A seed item left unwritten, and the constraint that refused it."""

    key: str
    reason: str


@dataclass(frozen=True)
class SeedWriteResult:
    """The items of one kind written, skipped and failed.

    ``skipped`` collides with a row already there; ``failed`` refers to a row that is not.
    """

    succeeded: list[str] = field(default_factory=list)
    skipped: list[SeedItemFailure] = field(default_factory=list)
    failed: list[SeedItemFailure] = field(default_factory=list)
