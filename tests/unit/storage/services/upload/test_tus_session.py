"""
Unit tests for the TUS upload session state model.

These tests cover the pure data-layer behavior of ``TusSessionState``:
computing the contiguous prefix offset, finding records by offset, and
serialization. Nothing here touches the filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ai.backend.common.types import TusSessionId
from ai.backend.storage.services.upload.types import (
    ChunkMetadata,
    TusSessionState,
)


def _make_chunk_metadata(offset: int, length: int, sha256: str = "x") -> ChunkMetadata:
    return ChunkMetadata(offset=offset, length=length, sha256=sha256)


@dataclass(frozen=True)
class _CommittedOffsetCase:
    records: list[ChunkMetadata]
    expected_prefix: int


class TestTusSessionStatePrefix:
    @pytest.mark.parametrize(
        "case",
        [
            # Empty session: nothing received yet, prefix is at 0.
            _CommittedOffsetCase(records=[], expected_prefix=0),
            # Single chunk at the start fills offsets [0, 100).
            _CommittedOffsetCase(
                records=[_make_chunk_metadata(0, 100)],
                expected_prefix=100,
            ),
            # Two adjacent chunks form a contiguous prefix [0, 150).
            _CommittedOffsetCase(
                records=[_make_chunk_metadata(0, 100), _make_chunk_metadata(100, 50)],
                expected_prefix=150,
            ),
            # Gap after a contiguous prefix: prefix ends at the gap, not at the
            # last entry's end.
            _CommittedOffsetCase(
                records=[_make_chunk_metadata(0, 100), _make_chunk_metadata(200, 50)],
                expected_prefix=100,
            ),
            # No chunk covers byte 0: there is no prefix to report.
            _CommittedOffsetCase(
                records=[_make_chunk_metadata(50, 100)],
                expected_prefix=0,
            ),
        ],
    )
    def test_committed_offset(self, case: _CommittedOffsetCase) -> None:
        state = TusSessionState(
            session_id=TusSessionId("s"), total_size=1024, committed_chunks=list(case.records)
        )
        assert state.committed_offset == case.expected_prefix


class TestFindAtOffset:
    def test_returns_record_at_matching_offset(self) -> None:
        rec = _make_chunk_metadata(100, 50)
        state = TusSessionState(
            session_id=TusSessionId("s"),
            total_size=1024,
            committed_chunks=[_make_chunk_metadata(0, 100, "a"), rec],
        )
        assert state.find_at_offset(100) == rec

    def test_returns_none_when_offset_not_present(self) -> None:
        state = TusSessionState(
            session_id=TusSessionId("s"),
            total_size=1024,
            committed_chunks=[_make_chunk_metadata(0, 100, "a")],
        )
        assert state.find_at_offset(500) is None
