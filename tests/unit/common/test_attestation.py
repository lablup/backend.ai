from __future__ import annotations

from typing import Any

import pytest

from ai.backend.common.attestation import (
    ATTESTATION_SOURCE,
    MAX_ATTESTATION_KEYS,
    MAX_ATTESTATION_STRING_LEN,
    build_attestation_status,
)


class TestBuildAttestationStatus:
    def test_none_stays_none(self) -> None:
        assert build_attestation_status(None) is None

    def test_source_is_forced(self) -> None:
        status = build_attestation_status({"attested": True, "source": "verified"})

        assert status == {"attested": True, "source": ATTESTATION_SOURCE}

    def test_nested_dict_of_primitives_is_kept(self) -> None:
        summary = {"claims_unverified": {"a": "x", "b": 1, "c": None}, "ok": 1.5}

        assert build_attestation_status(summary) == {**summary, "source": ATTESTATION_SOURCE}

    @pytest.mark.parametrize(
        "summary",
        [
            {f"k{i}": 1 for i in range(MAX_ATTESTATION_KEYS + 1)},
            {"long": "x" * (MAX_ATTESTATION_STRING_LEN + 1)},
            {"list": [1, 2]},
            {"deep": {"inner": {"too": "deep"}}},
            {"obj": object()},
            {"nested_long": {"v": "x" * (MAX_ATTESTATION_STRING_LEN + 1)}},
            {f"k{i}": "x" * MAX_ATTESTATION_STRING_LEN for i in range(MAX_ATTESTATION_KEYS)},
        ],
    )
    def test_oversize_or_unsupported_summary_is_dropped(self, summary: dict[str, Any]) -> None:
        assert build_attestation_status(summary) is None

    def test_sixteen_keys_are_kept(self) -> None:
        summary = {f"k{i}": i for i in range(MAX_ATTESTATION_KEYS)}

        status = build_attestation_status(summary)

        assert status is not None
        assert status["source"] == ATTESTATION_SOURCE

    def test_building_twice_is_stable(self) -> None:
        once = build_attestation_status({"a": 1})

        assert build_attestation_status(once) == once
