from __future__ import annotations

import csv
import io

import pytest

from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.export import (
    KeypairExportCSVRequest,
    ProjectExportCSVRequest,
    UserExportCSVRequest,
)


class TestUserCSVContentValidation:
    """Validate CSV content structure and encoding for user exports."""

    async def test_csv_has_requested_field_headers(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Downloaded CSV contains headers matching the requested fields."""
        requested_fields = ["uuid", "email"]
        request = UserExportCSVRequest(fields=requested_fields)
        raw = await admin_registry.export.download_users_csv(request)
        assert isinstance(raw, bytes)

        text = raw.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        headers = next(reader)
        for field in requested_fields:
            assert field in headers

    async def test_csv_utf8_encoding(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """CSV bytes are valid UTF-8."""
        request = UserExportCSVRequest(fields=["uuid", "email"])
        raw = await admin_registry.export.download_users_csv(request)
        text = raw.decode("utf-8-sig")
        assert len(text) > 0

    async def test_csv_contains_at_least_admin_row(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """The user CSV includes at least one data row (the admin user from fixtures)."""
        request = UserExportCSVRequest(fields=["uuid", "email"])
        raw = await admin_registry.export.download_users_csv(request)
        text = raw.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        headers = next(reader)
        rows = list(reader)
        assert len(headers) >= 2
        assert len(rows) >= 1

    async def test_regular_user_cannot_download_csv(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular users are blocked from exporting user CSV."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.export.download_users_csv(UserExportCSVRequest(fields=["uuid"]))


class TestProjectCSVContentValidation:
    """Validate CSV content for project exports."""

    async def test_project_csv_has_headers(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Downloaded project CSV contains field headers."""
        requested_fields = ["id", "name"]
        request = ProjectExportCSVRequest(fields=requested_fields)
        raw = await admin_registry.export.download_projects_csv(request)
        assert isinstance(raw, bytes)

        text = raw.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        headers = next(reader)
        for field in requested_fields:
            assert field in headers

    async def test_project_csv_contains_fixture_project(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """The project CSV includes at least one data row (the group/project from fixtures)."""
        request = ProjectExportCSVRequest(fields=["id", "name"])
        raw = await admin_registry.export.download_projects_csv(request)
        text = raw.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        _headers = next(reader)
        rows = list(reader)
        assert len(rows) >= 1


class TestKeypairCSVContentValidation:
    """Validate CSV content for keypair exports."""

    async def test_keypair_csv_has_headers_and_data(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Downloaded keypair CSV contains headers and at least one row."""
        requested_fields = ["access_key", "user_id"]
        request = KeypairExportCSVRequest(fields=requested_fields)
        raw = await admin_registry.export.download_keypairs_csv(request)
        assert isinstance(raw, bytes)

        text = raw.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        headers = next(reader)
        for field in requested_fields:
            assert field in headers
        rows = list(reader)
        assert len(rows) >= 1

    async def test_keypair_csv_does_not_expose_secret_key(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """When requesting specific fields, secret_key is not included unless asked."""
        request = KeypairExportCSVRequest(fields=["access_key", "user_id"])
        raw = await admin_registry.export.download_keypairs_csv(request)
        text = raw.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        headers = next(reader)
        assert "secret_key" not in headers
