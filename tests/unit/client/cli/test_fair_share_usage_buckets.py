"""Tests for fair share usage bucket CLI commands."""

from __future__ import annotations

from collections.abc import Callable

import click
from click.testing import CliRunner


class TestRgDomainUsageBucketListCommand:
    """Tests for rg-domain-usage list command date filter options."""

    def test_date_filter_options_recognized(
        self,
        runner: CliRunner,
        cli_entrypoint: Callable[[], click.Group],
    ) -> None:
        """Test that date filter options are properly recognized by the CLI."""
        result = runner.invoke(
            cli_entrypoint,
            [
                "fair-share",
                "rg-domain-usage",
                "list",
                "default",
                "--period-start-after",
                "2025-02-01",
                "--period-start-before",
                "2025-02-28",
            ],
        )

        # Should not fail with "no such option" error
        assert "no such option" not in result.output.lower()
        assert "--period-start-after" not in result.output  # Not an unrecognized option


class TestRgProjectUsageBucketListCommand:
    """Tests for rg-project-usage list command date filter options."""

    def test_date_filter_options_recognized(
        self,
        runner: CliRunner,
        cli_entrypoint: Callable[[], click.Group],
    ) -> None:
        """Test that date filter options are properly recognized by the CLI."""
        result = runner.invoke(
            cli_entrypoint,
            [
                "fair-share",
                "rg-project-usage",
                "list",
                "default",
                "test-domain",
                "--period-start-after",
                "2025-02-01",
            ],
        )

        # Should not fail with "no such option" error
        assert "no such option" not in result.output.lower()


class TestRgUserUsageBucketListCommand:
    """Tests for rg-user-usage list command date filter options."""

    def test_date_filter_options_recognized(
        self,
        runner: CliRunner,
        cli_entrypoint: Callable[[], click.Group],
    ) -> None:
        """Test that date filter options are properly recognized by the CLI."""
        project_id = "00000000-0000-0000-0000-000000000001"
        result = runner.invoke(
            cli_entrypoint,
            [
                "fair-share",
                "rg-user-usage",
                "list",
                "default",
                "test-domain",
                project_id,
                "--period-start-before",
                "2025-02-28",
            ],
        )

        # Should not fail with "no such option" error
        assert "no such option" not in result.output.lower()
