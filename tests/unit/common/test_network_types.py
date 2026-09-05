"""The shared network types the manager and the agent both read.

One definition, because the two ends disagreeing about what a value means is the failure these
exist to prevent.
"""

from __future__ import annotations

from ai.backend.common.network.types import OverlayEncryptionPolicy


class TestTheOverlayEncryptionPolicy:
    """A boolean could not hold both "encrypt this" and "encrypt this if you can", so it meant the
    weaker one for everybody: an operator who wrote `true` because these sessions are confidential
    was handed plain VXLAN and a log line the moment one agent turned out to be old."""

    def test_nothing_configured_is_required(self) -> None:
        assert OverlayEncryptionPolicy.parse(None) is OverlayEncryptionPolicy.REQUIRED

    def test_true_is_required(self) -> None:
        # What whoever wrote it meant by it.
        assert OverlayEncryptionPolicy.parse(True) is OverlayEncryptionPolicy.REQUIRED

    def test_false_is_disabled(self) -> None:
        assert OverlayEncryptionPolicy.parse(False) is OverlayEncryptionPolicy.DISABLED

    def test_the_names_parse(self) -> None:
        for name, expected in (
            ("required", OverlayEncryptionPolicy.REQUIRED),
            ("prefer", OverlayEncryptionPolicy.PREFER),
            ("disabled", OverlayEncryptionPolicy.DISABLED),
        ):
            assert OverlayEncryptionPolicy.parse(name) is expected

    def test_case_and_whitespace_do_not_matter(self) -> None:
        assert OverlayEncryptionPolicy.parse("  Prefer ") is OverlayEncryptionPolicy.PREFER

    def test_a_typo_is_required_not_permission(self) -> None:
        # A misspelling in a security setting must not read as the weakest option.
        assert OverlayEncryptionPolicy.parse("prefered") is OverlayEncryptionPolicy.REQUIRED
        assert OverlayEncryptionPolicy.parse("") is OverlayEncryptionPolicy.REQUIRED
