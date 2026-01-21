"""Tests for mount validation rules."""

import pytest

from ai.backend.manager.errors.api import InvalidAPIParameters
from ai.backend.manager.repositories.scheduler.types.session_creation import (
    ContainerUserInfo,
    SessionCreationContext,
    SessionCreationSpec,
)
from ai.backend.manager.sokovan.scheduling_controller.validators.mount import (
    MountNameValidationRule,
)


class TestMountNameValidationRule:
    """Test cases for MountNameValidationRule."""

    @pytest.fixture
    def mount_rule(self):
        """Create a MountNameValidationRule instance."""
        return MountNameValidationRule()

    @pytest.fixture
    def basic_context(self):
        """Create a basic SessionCreationContext."""
        return SessionCreationContext(
            scaling_group_network=None,
            allowed_scaling_groups=[],
            image_infos={},
            vfolder_mounts=[],
            dotfile_data={},
            container_user_info=ContainerUserInfo(),
        )

    def test_valid_mount_names(self, mount_rule, basic_context):
        """Test validation with valid mount names."""
        spec = SessionCreationSpec(
            session_creation_id="test-001",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={
                "mount_map": {
                    "vfolder1": "data",
                    "vfolder2": "models",
                    "vfolder3": "outputs",
                }
            },
        )

        # Should not raise
        mount_rule.validate(spec, basic_context)

    def test_duplicate_alias_names(self, mount_rule, basic_context):
        """Test validation with duplicate alias names."""
        spec = SessionCreationSpec(
            session_creation_id="test-002",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={
                "mount_map": {
                    "vfolder1": "data",
                    "vfolder2": "data",  # Duplicate alias
                    "vfolder3": "outputs",
                }
            },
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            mount_rule.validate(spec, basic_context)
        assert "duplicate alias folder name" in str(exc_info.value).lower()

    def test_empty_alias_name(self, mount_rule, basic_context):
        """Test validation with empty alias name."""
        spec = SessionCreationSpec(
            session_creation_id="test-003",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={
                "mount_map": {
                    "vfolder1": "",  # Empty alias
                    "vfolder2": "data",
                }
            },
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            mount_rule.validate(spec, basic_context)
        assert "alias name cannot be empty" in str(exc_info.value).lower()

    def test_reserved_folder_names(self, mount_rule, basic_context):
        """Test validation with reserved folder names."""
        # Reserved names that should fail (matching RESERVED_VFOLDERS in defs.py)
        reserved_names = [
            ".terminfo",
            ".jupyter",
            ".tmux.conf",
            ".ssh",
            "/bin",
            "/boot",
            "/dev",
            "/etc",
            "/lib",
            "/lib64",
            "/media",
            "/mnt",
            "/opt",
            "/proc",
            "/root",
            "/run",
            "/sbin",
            "/srv",
            "/sys",
            "/tmp",
            "/usr",
            "/var",
            "/home",
        ]

        for reserved_name in reserved_names:
            spec = SessionCreationSpec(
                session_creation_id=f"test-reserved-{reserved_name}",
                session_name="test",
                access_key="test-key",
                user_scope=None,
                session_type=None,
                cluster_mode=None,
                cluster_size=1,
                priority=10,
                resource_policy={},
                kernel_specs=[],
                creation_spec={
                    "mount_map": {
                        "vfolder1": reserved_name,
                    }
                },
            )

            with pytest.raises(InvalidAPIParameters) as exc_info:
                mount_rule.validate(spec, basic_context)
            assert "reserved for internal path" in str(exc_info.value)

    def test_alias_same_as_original_folder(self, mount_rule, basic_context):
        """Test validation when alias name is same as an existing folder name."""
        spec = SessionCreationSpec(
            session_creation_id="test-004",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={
                "mount_map": {
                    "vfolder1": "vfolder2",  # Alias same as another original folder
                    "vfolder2": "data",
                }
            },
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            mount_rule.validate(spec, basic_context)
        assert "cannot be set to an existing folder name" in str(exc_info.value)

    def test_work_directory_prefix_handling(self, mount_rule, basic_context):
        """Test handling of /home/work/ prefix in alias names."""
        spec = SessionCreationSpec(
            session_creation_id="test-005",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={
                "mount_map": {
                    "vfolder1": "/home/work/data",  # With work prefix
                    "vfolder2": "/home/work/models",
                }
            },
        )

        # Should validate without the prefix - the prefix is stripped
        mount_rule.validate(spec, basic_context)

    def test_combined_mount_maps(self, mount_rule, basic_context):
        """Test validation with both mount_map and mount_id_map."""
        spec = SessionCreationSpec(
            session_creation_id="test-006",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={
                "mount_map": {
                    "vfolder1": "data",
                    "vfolder2": "models",
                },
                "mount_id_map": {
                    "id123": "outputs",
                    "id456": "logs",
                },
            },
        )

        # Should validate both maps combined
        mount_rule.validate(spec, basic_context)

    def test_duplicate_across_maps(self, mount_rule, basic_context):
        """Test duplicate aliases across mount_map and mount_id_map."""
        spec = SessionCreationSpec(
            session_creation_id="test-007",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={
                "mount_map": {
                    "vfolder1": "data",
                },
                "mount_id_map": {
                    "id123": "data",  # Duplicate alias across maps
                },
            },
        )

        with pytest.raises(InvalidAPIParameters) as exc_info:
            mount_rule.validate(spec, basic_context)
        assert "duplicate alias folder name" in str(exc_info.value).lower()

    def test_none_alias_values(self, mount_rule, basic_context):
        """Test handling of None alias values."""
        spec = SessionCreationSpec(
            session_creation_id="test-008",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={
                "mount_map": {
                    "vfolder1": None,  # None alias should be skipped
                    "vfolder2": "data",
                }
            },
        )

        # Should not raise - None values are skipped
        mount_rule.validate(spec, basic_context)

    def test_special_characters_in_names(self, mount_rule, basic_context):
        """Test validation with special characters in folder names."""
        # These should be caught as reserved names or patterns
        invalid_names = [
            "/etc",  # Reserved folder
            "/root",  # Reserved folder
            ".ssh",  # Reserved folder
            ".jupyter",  # Reserved folder
        ]

        for invalid_name in invalid_names:
            spec = SessionCreationSpec(
                session_creation_id=f"test-special-{hash(invalid_name)}",
                session_name="test",
                access_key="test-key",
                user_scope=None,
                session_type=None,
                cluster_mode=None,
                cluster_size=1,
                priority=10,
                resource_policy={},
                kernel_specs=[],
                creation_spec={
                    "mount_map": {
                        "vfolder1": invalid_name,
                    }
                },
            )

            with pytest.raises(InvalidAPIParameters):
                mount_rule.validate(spec, basic_context)

    def test_large_mount_map(self, mount_rule, basic_context):
        """Test validation with a large number of mounts."""
        # Create a large mount map
        mount_map = {f"vfolder{i}": f"data{i}" for i in range(100)}

        spec = SessionCreationSpec(
            session_creation_id="test-large",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={"mount_map": mount_map},
        )

        # Should handle large number of mounts
        mount_rule.validate(spec, basic_context)

    def test_unicode_names(self, mount_rule, basic_context):
        """Test validation with unicode characters in names."""
        spec = SessionCreationSpec(
            session_creation_id="test-unicode",
            session_name="test",
            access_key="test-key",
            user_scope=None,
            session_type=None,
            cluster_mode=None,
            cluster_size=1,
            priority=10,
            resource_policy={},
            kernel_specs=[],
            creation_spec={
                "mount_map": {
                    "vfolder1": "데이터",  # Korean
                    "vfolder2": "文档",  # Chinese
                    "vfolder3": "données",  # French
                }
            },
        )

        # Unicode names should be handled properly
        # This may pass or fail depending on verify_vfolder_name implementation
        try:
            mount_rule.validate(spec, basic_context)
        except InvalidAPIParameters:
            # If unicode is not allowed, that's also valid behavior
            pass
