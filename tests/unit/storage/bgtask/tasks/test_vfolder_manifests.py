from __future__ import annotations

from uuid import UUID

import pytest

from ai.backend.common.types import QuotaScopeID, VFolderID
from ai.backend.storage.bgtask.tasks.clone import VFolderCloneManifest
from ai.backend.storage.bgtask.tasks.delete import VFolderDeleteManifest


class TestVFolderCloneManifest:
    """Tests for VFolderCloneManifest serialization/deserialization."""

    @pytest.fixture
    def sample_vfolder_id_with_quota(self) -> VFolderID:
        """Sample VFolderID with quota scope."""
        return VFolderID(
            QuotaScopeID.parse("project:12345678123456781234567812345678"),
            UUID("12345678-1234-5678-1234-567812345678"),
        )

    @pytest.fixture
    def sample_vfolder_id_without_quota(self) -> VFolderID:
        """Sample VFolderID without quota scope."""
        return VFolderID(None, UUID("87654321-4321-8765-4321-876543218765"))

    def test_manifest_creation_with_quota(self, sample_vfolder_id_with_quota: VFolderID) -> None:
        """Test manifest can be created with VFolderID that has quota scope."""
        manifest = VFolderCloneManifest(
            volume="local",
            src_vfolder=sample_vfolder_id_with_quota,
            dst_vfolder=sample_vfolder_id_with_quota,
        )
        assert manifest.src_vfolder == sample_vfolder_id_with_quota
        assert manifest.dst_vfolder == sample_vfolder_id_with_quota

    def test_manifest_creation_without_quota(
        self, sample_vfolder_id_without_quota: VFolderID
    ) -> None:
        """Test manifest can be created with VFolderID without quota scope."""
        manifest = VFolderCloneManifest(
            volume="local",
            src_vfolder=sample_vfolder_id_without_quota,
            dst_vfolder=sample_vfolder_id_without_quota,
        )
        assert manifest.src_vfolder == sample_vfolder_id_without_quota
        assert manifest.dst_vfolder == sample_vfolder_id_without_quota

    def test_manifest_serialization_with_quota(
        self, sample_vfolder_id_with_quota: VFolderID
    ) -> None:
        """Test manifest serialization with VFolderID that has quota scope."""
        manifest = VFolderCloneManifest(
            volume="local",
            src_vfolder=sample_vfolder_id_with_quota,
            dst_vfolder=sample_vfolder_id_with_quota,
        )

        # Serialize to dict
        data = manifest.model_dump(mode="json")
        assert data["volume"] == "local"
        assert data["src_vfolder"] == str(sample_vfolder_id_with_quota)
        assert data["dst_vfolder"] == str(sample_vfolder_id_with_quota)
        # Check format: "project:test-project/12345678123456781234567812345678"
        assert "/" in data["src_vfolder"]

    def test_manifest_serialization_without_quota(
        self, sample_vfolder_id_without_quota: VFolderID
    ) -> None:
        """Test manifest serialization with VFolderID without quota scope."""
        manifest = VFolderCloneManifest(
            volume="local",
            src_vfolder=sample_vfolder_id_without_quota,
            dst_vfolder=sample_vfolder_id_without_quota,
        )

        # Serialize to dict
        data = manifest.model_dump(mode="json")
        assert data["volume"] == "local"
        assert data["src_vfolder"] == str(sample_vfolder_id_without_quota)
        assert data["dst_vfolder"] == str(sample_vfolder_id_without_quota)
        # Check format: just the UUID hex (no quota scope prefix)
        assert "/" not in data["src_vfolder"]

    def test_manifest_deserialization_with_quota(
        self, sample_vfolder_id_with_quota: VFolderID
    ) -> None:
        """Test manifest deserialization from string with quota scope."""
        data = {
            "volume": "local",
            "src_vfolder": str(sample_vfolder_id_with_quota),
            "dst_vfolder": str(sample_vfolder_id_with_quota),
        }

        # Deserialize from dict
        manifest = VFolderCloneManifest.model_validate(data)
        assert manifest.volume == "local"
        assert manifest.src_vfolder == sample_vfolder_id_with_quota
        assert manifest.dst_vfolder == sample_vfolder_id_with_quota

    def test_manifest_deserialization_without_quota(
        self, sample_vfolder_id_without_quota: VFolderID
    ) -> None:
        """Test manifest deserialization from string without quota scope."""
        data = {
            "volume": "local",
            "src_vfolder": str(sample_vfolder_id_without_quota),
            "dst_vfolder": str(sample_vfolder_id_without_quota),
        }

        # Deserialize from dict
        manifest = VFolderCloneManifest.model_validate(data)
        assert manifest.volume == "local"
        assert manifest.src_vfolder == sample_vfolder_id_without_quota
        assert manifest.dst_vfolder == sample_vfolder_id_without_quota

    def test_manifest_roundtrip_with_quota(self, sample_vfolder_id_with_quota: VFolderID) -> None:
        """Test full serialization/deserialization roundtrip with quota scope."""
        original = VFolderCloneManifest(
            volume="local",
            src_vfolder=sample_vfolder_id_with_quota,
            dst_vfolder=sample_vfolder_id_with_quota,
        )

        # Serialize and deserialize
        data = original.model_dump(mode="json")
        restored = VFolderCloneManifest.model_validate(data)

        # Check equality
        assert restored.volume == original.volume
        assert restored.src_vfolder == original.src_vfolder
        assert restored.dst_vfolder == original.dst_vfolder


class TestVFolderDeleteManifest:
    """Tests for VFolderDeleteManifest serialization/deserialization."""

    @pytest.fixture
    def sample_vfolder_id(self) -> VFolderID:
        """Sample VFolderID for testing."""
        return VFolderID(
            QuotaScopeID.parse("user:abcdef12abcdef12abcdef1234567890"),
            UUID("abcdef12-abcd-ef12-abcd-ef1234567890"),
        )

    def test_manifest_creation(self, sample_vfolder_id: VFolderID) -> None:
        """Test manifest can be created with VFolderID."""
        manifest = VFolderDeleteManifest(
            volume="local",
            vfolder_id=sample_vfolder_id,
        )
        assert manifest.volume == "local"
        assert manifest.vfolder_id == sample_vfolder_id

    def test_manifest_serialization(self, sample_vfolder_id: VFolderID) -> None:
        """Test manifest serialization."""
        manifest = VFolderDeleteManifest(
            volume="local",
            vfolder_id=sample_vfolder_id,
        )

        # Serialize to dict
        data = manifest.model_dump(mode="json")
        assert data["volume"] == "local"
        assert data["vfolder_id"] == str(sample_vfolder_id)
        assert "/" in data["vfolder_id"]  # Has quota scope

    def test_manifest_deserialization(self, sample_vfolder_id: VFolderID) -> None:
        """Test manifest deserialization from string."""
        data = {
            "volume": "local",
            "vfolder_id": str(sample_vfolder_id),
        }

        # Deserialize from dict
        manifest = VFolderDeleteManifest.model_validate(data)
        assert manifest.volume == "local"
        assert manifest.vfolder_id == sample_vfolder_id

    def test_manifest_roundtrip(self, sample_vfolder_id: VFolderID) -> None:
        """Test full serialization/deserialization roundtrip."""
        original = VFolderDeleteManifest(
            volume="local",
            vfolder_id=sample_vfolder_id,
        )

        # Serialize and deserialize
        data = original.model_dump(mode="json")
        restored = VFolderDeleteManifest.model_validate(data)

        # Check equality
        assert restored.volume == original.volume
        assert restored.vfolder_id == original.vfolder_id
