"""
TUS upload session state model.

This module defines the pure data classes that describe an in-flight upload
session — what byte ranges have been received, how that maps to the standard
TUS ``Upload-Offset`` semantics, and which ranges are still missing. No I/O
or locking lives here; the storage class that mutates this state on disk
arrives in a follow-up change.

The model is the source of truth for an upload session: instead of inferring
progress from the size of a single temp file (which is racy on a shared NFS
mount with multiple Storage Proxy replicas), every committed chunk is recorded
as an explicit ``ChunkRecord`` keyed by its absolute byte offset.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Self

from ai.backend.storage.errors.upload import UploadSessionCorruptedError


@dataclass(frozen=True, slots=True)
class ChunkRecord:
    offset: int
    length: int
    sha256: str

    @property
    def end(self) -> int:
        return self.offset + self.length

    def to_json(self) -> dict[str, int | str]:
        return {"offset": self.offset, "length": self.length, "sha256": self.sha256}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        return cls(
            offset=int(data["offset"]),
            length=int(data["length"]),
            sha256=str(data["sha256"]),
        )


@dataclass(frozen=True, slots=True)
class SessionState:
    session_id: str
    total_size: int
    received: tuple[ChunkRecord, ...]
    status: str

    @property
    def committed_offset(self) -> int:
        """End offset of the largest contiguous prefix from byte 0."""
        cursor = 0
        for rec in self.received:
            if rec.offset != cursor:
                break
            cursor = rec.end
        return cursor

    @property
    def is_complete(self) -> bool:
        return self.status == "completed" or (
            self.committed_offset >= self.total_size and self.total_size > 0
        )

    def find_at_offset(self, offset: int) -> ChunkRecord | None:
        for rec in self.received:
            if rec.offset == offset:
                return rec
            if rec.offset > offset:
                return None
        return None

    def missing_ranges(self) -> list[tuple[int, int]]:
        """
        Return the list of ``(offset, length)`` byte ranges in
        ``[0, total_size)`` that are NOT yet covered by any received chunk.

        Overlapping or out-of-bounds received chunks are tolerated: ranges
        are coalesced and clipped against the declared total size.
        """
        if self.total_size <= 0:
            return []
        covered: list[tuple[int, int]] = []
        for rec in self.received:
            start = max(0, rec.offset)
            end = min(self.total_size, rec.end)
            if start < end:
                covered.append((start, end))
        if not covered:
            return [(0, self.total_size)]
        covered.sort()
        merged: list[tuple[int, int]] = [covered[0]]
        for start, end in covered[1:]:
            last_start, last_end = merged[-1]
            if start <= last_end:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))
        gaps: list[tuple[int, int]] = []
        cursor = 0
        for start, end in merged:
            if cursor < start:
                gaps.append((cursor, start - cursor))
            cursor = end
        if cursor < self.total_size:
            gaps.append((cursor, self.total_size - cursor))
        return gaps

    def progress_percent(self) -> float:
        if self.total_size <= 0:
            return 100.0
        return round(100.0 * self.committed_offset / self.total_size, 2)

    def to_json(self) -> dict[str, object]:
        return {
            "session": self.session_id,
            "total_size": self.total_size,
            "received": [rec.to_json() for rec in self.received],
            "status": self.status,
            "updated_at": datetime.now(UTC).isoformat(),
        }

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        raw_received = data.get("received", [])
        if not isinstance(raw_received, list):
            raise UploadSessionCorruptedError("'received' must be a list")
        records: list[ChunkRecord] = []
        for item in raw_received:
            if not isinstance(item, dict):
                raise UploadSessionCorruptedError("malformed chunk record")
            records.append(ChunkRecord.from_json(item))
        records.sort(key=lambda r: r.offset)
        return cls(
            session_id=str(data["session"]),
            total_size=int(data["total_size"]),
            received=tuple(records),
            status=str(data.get("status", "pending")),
        )

    @classmethod
    def empty(cls, session_id: str, total_size: int) -> Self:
        return cls(
            session_id=session_id,
            total_size=total_size,
            received=(),
            status="pending",
        )

    def with_record(self, record: ChunkRecord) -> Self:
        merged = list(self.received)
        merged.append(record)
        merged.sort(key=lambda r: r.offset)
        return dataclasses.replace(self, received=tuple(merged))

    def with_status(self, status: str) -> Self:
        return dataclasses.replace(self, status=status)


@dataclass(frozen=True, slots=True)
class ChunkAcceptance:
    """Result of attempting to commit a chunk into a session."""

    state: SessionState
    committed: bool  # False means duplicate (idempotent) replay
    completed_now: bool  # True if this commit just completed the upload
