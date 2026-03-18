from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.common.netns import setns


class TestSetns:
    """Tests for setns() return value checking."""

    def test_setns_raises_on_failure(self) -> None:
        """Verify setns() raises OSError when libc.setns() returns -1."""
        mock_libc = MagicMock()
        mock_libc.setns.return_value = -1

        with (
            patch("ai.backend.common.netns._get_libc", return_value=mock_libc),
            patch("ctypes.get_errno", return_value=1),
            pytest.raises(OSError, match="setns\\(\\) failed"),
        ):
            setns(42)

    def test_setns_succeeds_on_zero_return(self) -> None:
        """Verify setns() does not raise when libc.setns() returns 0."""
        mock_libc = MagicMock()
        mock_libc.setns.return_value = 0

        with patch("ai.backend.common.netns._get_libc", return_value=mock_libc):
            setns(42)

        mock_libc.setns.assert_called_once()
