"""TUS upload session data types.

Holds the state schemas (`TusSessionState`, `ChunkMetadata`, `WrittenChunk`,
`ChunkCommitResult`) that the engine reads/writes, plus `TusUploadSessionArgs`
— the construction-time dependency bundle for `TusUploadSession`. The args
dataclass references I/O collaborators (Valkey client, lock factory, session
dir path) but performs no I/O of its own; the state schemas are pure data."""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Self, override

from pydantic import ConfigDict, Field

from ai.backend.common.clients.valkey_client.valkey_tus import ValkeyTusClient
from ai.backend.common.exception import BackendAIError
from ai.backend.common.lock import DistributedLockFactory
from ai.backend.common.types import (
    BackendAISchema,
    SchemaValidationFailureInfo,
    TusSessionId,
)
from ai.backend.storage.errors.upload import UploadSessionCorruptedError


class UploadStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ChunkMetadata(BackendAISchema):
    model_config = ConfigDict(frozen=True)

    offset: int
    length: int
    sha256: str

    @property
    def end(self) -> int:
        return self.offset + self.length


class TusSessionState(BackendAISchema):
    session_id: TusSessionId
    total_size: int
    committed_chunks: list[ChunkMetadata] = Field(default_factory=list)
    status: UploadStatus = UploadStatus.IN_PROGRESS

    @override
    @classmethod
    def build_validation_error(cls, info: SchemaValidationFailureInfo) -> BackendAIError:
        # Stored session metadata that fails to parse is server-side corruption
        # (500), not a client error, so map the ValidationError accordingly.
        return UploadSessionCorruptedError(
            f"upload session metadata is malformed: {info.summary}",
            extra_data={"errors": info.errors},
        )

    @property
    def committed_offset(self) -> int:
        """End offset of the largest contiguous prefix from byte 0.

        Not the same as the last entry's ``end``: out-of-order commits (multi-
        replica race, retry/resume, partial re-send via ``/upload/status``) can
        leave gaps in ``committed_chunks``. We must stop at the first gap so the
        value matches TUS ``Upload-Offset`` semantics ("send the next chunk from
        here") — using last-entry-end would tell the client to skip past gaps
        and drop data.
        """
        cursor = 0
        for rec in self.committed_chunks:
            if rec.offset != cursor:
                break
            cursor = rec.end
        return cursor

    def find_at_offset(self, offset: int) -> ChunkMetadata | None:
        for rec in self.committed_chunks:
            if rec.offset == offset:
                return rec
            if rec.offset > offset:
                return None
        return None

    @classmethod
    def empty(cls, session_id: TusSessionId, total_size: int) -> Self:
        return cls(session_id=session_id, total_size=total_size)

    def append_chunk(self, chunk: ChunkMetadata) -> None:
        """Insert ``chunk`` at the correct sorted position to keep
        ``committed_chunks`` ordered by offset. The sortedness invariant is
        what ``committed_offset`` and ``find_at_offset`` rely on."""
        bisect.insort(self.committed_chunks, chunk, key=lambda r: r.offset)

    def set_complete(self) -> None:
        """Mark the upload session as fully received and assembled."""
        self.status = UploadStatus.COMPLETED


@dataclass(frozen=True, slots=True)
class ChunkCommitResult:
    """Result of attempting to commit a chunk into a session."""

    state: TusSessionState
    committed: bool  # False means duplicate (idempotent) replay
    is_final_commit: bool  # True if this commit just completed the upload


@dataclass(frozen=True, slots=True)
class WrittenChunk:
    """
    Result of :meth:`TusUploadSession.write_temp_chunk`: the staged temp file
    path plus the byte count actually drained and its SHA-256 digest.
    """

    path: Path
    length: int
    sha256: str


@dataclass(frozen=True, slots=True)
class TusUploadSessionArgs:
    session_dir: Path
    session_id: TusSessionId
    total_size: int
    valkey_client: ValkeyTusClient
    lock_factory: DistributedLockFactory
