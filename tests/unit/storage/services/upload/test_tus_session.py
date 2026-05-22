"""
Unit tests for the TUS upload session state model.

These tests cover the pure data-layer behavior of ``SessionState``:
computing the contiguous prefix offset, finding records by offset, gap
analysis (``missing_ranges``), and progress reporting. Nothing here touches
the filesystem.
"""

from __future__ import annotations

import json

import pytest

from ai.backend.storage.errors.upload import UploadSessionCorruptedError
from ai.backend.storage.services.upload.tus_session import (
    ChunkRecord,
    SessionState,
)


class TestSessionStatePrefix:
    @pytest.mark.parametrize(
        ("records", "expected_prefix"),
        [
            ([], 0),
            ([ChunkRecord(0, 100, "x")], 100),
            ([ChunkRecord(0, 100, "x"), ChunkRecord(100, 50, "y")], 150),
            # Gap after a contiguous prefix: prefix ends at the gap.
            ([ChunkRecord(0, 100, "x"), ChunkRecord(200, 50, "y")], 100),
            # No prefix from byte 0.
            ([ChunkRecord(50, 100, "x")], 0),
        ],
    )
    def test_committed_offset(self, records: list[ChunkRecord], expected_prefix: int) -> None:
        state = SessionState(
            session_id="s",
            total_size=1024,
            received=tuple(records),
            status="pending",
        )
        assert state.committed_offset == expected_prefix


class TestFindAtOffset:
    def test_returns_record_at_matching_offset(self) -> None:
        rec = ChunkRecord(100, 50, "x")
        state = SessionState(
            session_id="s",
            total_size=1024,
            received=(ChunkRecord(0, 100, "a"), rec),
            status="pending",
        )
        assert state.find_at_offset(100) == rec

    def test_returns_none_when_offset_not_present(self) -> None:
        state = SessionState(
            session_id="s",
            total_size=1024,
            received=(ChunkRecord(0, 100, "a"),),
            status="pending",
        )
        assert state.find_at_offset(500) is None


class TestMissingRanges:
    @pytest.mark.parametrize(
        ("total_size", "records", "expected"),
        [
            # Empty session: the whole declared size is missing.
            (1000, [], [(0, 1000)]),
            # Single chunk at start.
            (1000, [ChunkRecord(0, 400, "x")], [(400, 600)]),
            # Single chunk in the middle.
            (1000, [ChunkRecord(200, 300, "x")], [(0, 200), (500, 500)]),
            # Contiguous prefix.
            (1000, [ChunkRecord(0, 400, "x"), ChunkRecord(400, 100, "y")], [(500, 500)]),
            # Two disjoint chunks leaving two gaps.
            (
                1000,
                [ChunkRecord(0, 200, "x"), ChunkRecord(500, 300, "y")],
                [(200, 300), (800, 200)],
            ),
            # Fully complete: no gaps.
            (500, [ChunkRecord(0, 500, "x")], []),
            # Overlapping/duplicate ranges are coalesced.
            (
                1000,
                [ChunkRecord(0, 600, "x"), ChunkRecord(400, 200, "y")],
                [(600, 400)],
            ),
            # Record extending past total_size is clipped.
            (1000, [ChunkRecord(800, 500, "x")], [(0, 800)]),
        ],
    )
    def test_missing_ranges(
        self,
        total_size: int,
        records: list[ChunkRecord],
        expected: list[tuple[int, int]],
    ) -> None:
        state = SessionState(
            session_id="s",
            total_size=total_size,
            received=tuple(records),
            status="pending",
        )
        assert state.missing_ranges() == expected

    @pytest.mark.parametrize(
        ("total_size", "records", "expected_percent"),
        [
            (1000, [], 0.0),
            (1000, [ChunkRecord(0, 250, "x")], 25.0),
            (1000, [ChunkRecord(0, 500, "x"), ChunkRecord(500, 500, "y")], 100.0),
            # Non-contiguous prefix only counts the contiguous head.
            (1000, [ChunkRecord(500, 500, "x")], 0.0),
            # Zero-size sessions are reported as 100%.
            (0, [], 100.0),
        ],
    )
    def test_progress_percent(
        self,
        total_size: int,
        records: list[ChunkRecord],
        expected_percent: float,
    ) -> None:
        state = SessionState(
            session_id="s",
            total_size=total_size,
            received=tuple(records),
            status="pending",
        )
        assert state.progress_percent() == expected_percent


class TestRoundtripJson:
    def test_to_json_then_from_json_preserves_records(self) -> None:
        state = SessionState(
            session_id="abc",
            total_size=2048,
            received=(
                ChunkRecord(0, 1024, "deadbeef"),
                ChunkRecord(1024, 1024, "feedface"),
            ),
            status="pending",
        )
        roundtrip = SessionState.from_json(state.to_json())
        assert roundtrip.session_id == state.session_id
        assert roundtrip.total_size == state.total_size
        assert roundtrip.received == state.received
        assert roundtrip.status == state.status

    def test_from_json_sorts_received_by_offset(self) -> None:
        raw = {
            "session": "abc",
            "total_size": 2048,
            "status": "pending",
            "received": [
                {"offset": 1024, "length": 1024, "sha256": "second"},
                {"offset": 0, "length": 1024, "sha256": "first"},
            ],
        }
        state = SessionState.from_json(raw)
        assert [r.offset for r in state.received] == [0, 1024]

    def test_from_json_rejects_non_list_received(self) -> None:
        with pytest.raises(UploadSessionCorruptedError):
            SessionState.from_json({"session": "s", "total_size": 0, "received": "x"})

    def test_from_json_rejects_malformed_record(self) -> None:
        with pytest.raises(UploadSessionCorruptedError):
            SessionState.from_json({"session": "s", "total_size": 0, "received": ["not a dict"]})

    def test_to_json_is_json_serializable(self) -> None:
        state = SessionState.empty("abc", 1024)
        # Should not raise.
        json.dumps(state.to_json())


class TestWithModifiers:
    def test_with_record_keeps_received_sorted(self) -> None:
        state = SessionState.empty("s", 3000)
        state = state.with_record(ChunkRecord(2000, 500, "c"))
        state = state.with_record(ChunkRecord(0, 1000, "a"))
        state = state.with_record(ChunkRecord(1000, 1000, "b"))
        assert [r.offset for r in state.received] == [0, 1000, 2000]

    def test_with_status_returns_updated_copy(self) -> None:
        state = SessionState.empty("s", 1024)
        updated = state.with_status("completed")
        assert state.status == "pending"
        assert updated.status == "completed"
        assert updated.session_id == state.session_id
