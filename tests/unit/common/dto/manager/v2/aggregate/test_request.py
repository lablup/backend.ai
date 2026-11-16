"""The aggregate group inputs reject a bucket length below a second and an unknown time zone."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai.backend.common.dto.manager.v2.aggregate.request import DateTimeGroup
from ai.backend.common.exception import BackendAISchemaValidationFailed


class TestDateTimeGroup:
    def test_a_known_time_zone_is_kept(self) -> None:
        group = DateTimeGroup(interval_seconds=60, timezone="Asia/Seoul")

        assert group.timezone == "Asia/Seoul"

    def test_an_unknown_time_zone_is_rejected(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            DateTimeGroup(interval_seconds=60, timezone="Mars/Olympus")

    def test_an_interval_below_one_second_is_rejected(self) -> None:
        with pytest.raises((BackendAISchemaValidationFailed, ValidationError)):
            DateTimeGroup(interval_seconds=0)
