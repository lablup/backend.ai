from __future__ import annotations

import pytest

from ai.backend.manager.data.project.types import ProjectType


class TestProjectType:
    def test_personal_value(self) -> None:
        assert ProjectType.PERSONAL.value == "personal"

    def test_missing_accepts_upper_form(self) -> None:
        assert ProjectType("PERSONAL") is ProjectType.PERSONAL
        assert ProjectType("personal") is ProjectType.PERSONAL

    def test_missing_returns_none_for_unknown(self) -> None:
        with pytest.raises(ValueError):
            ProjectType("no-such-type")
