from __future__ import annotations

from dataclasses import dataclass

import pytest

from ai.backend.appproxy.coordinator.config import ContentEncodingConfig


@dataclass(frozen=True)
class _RejectedEncodingsCase:
    configured: list[str]
    expected: list[str]


class TestContentEncodingConfig:
    @pytest.mark.parametrize(
        "case",
        [
            _RejectedEncodingsCase(configured=[], expected=[]),
            _RejectedEncodingsCase(configured=["br"], expected=["br"]),
            _RejectedEncodingsCase(configured=[" br ", "zstd "], expected=["br", "zstd"]),
        ],
        ids=lambda case: ",".join(case.configured) or "empty",
    )
    def test_strips_whitespace_from_rejected_encodings(self, case: _RejectedEncodingsCase) -> None:
        config = ContentEncodingConfig.model_validate({"rejected_encodings": case.configured})

        assert config.rejected_encodings == case.expected
