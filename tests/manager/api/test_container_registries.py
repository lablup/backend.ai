import pytest

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.manager.errors.container_registry import (
    InvalidContainerRegistryProject,
    InvalidContainerRegistryURL,
)
from ai.backend.manager.models.container_registry import (
    ContainerRegistryValidator,
    ContainerRegistryValidatorArgs,
)


class TestContainerRegistryValidator:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "valid_url",
        [
            # Standard HTTP/HTTPS URLs
            "http://example.com",
            "https://example.com",
            "https://registry.example.com",
            "http://localhost:5000",
            "https://docker.io",
            # IP addresses (should be allowed)
            "192.168.1.100",
            "192.168.1.100:5000",
            "10.0.0.1:8080",
            "127.0.0.1",
            "127.0.0.1:5000",
            # Simple hostnames (should be allowed)
            "abc",
            "localhost",
            "registry",
            "my-registry",
            "registry.local",
            # URLs with ports
            "example.com:8080",
            "registry.example.com:443",
            # URLs with paths
            "https://example.com/registry",
            "http://localhost:5000/v2",
        ],
    )
    async def test_valid_urls(self, valid_url: str) -> None:
        """Test that valid URLs pass validation."""
        args = ContainerRegistryValidatorArgs(
            url=valid_url, type=ContainerRegistryType.DOCKER, project=None
        )
        validator = ContainerRegistryValidator(args)
        # Should not raise any exception
        validator.validate()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_url",
        [
            # Empty or whitespace-only URLs
            "",
            "   ",
            # Malformed URLs that fail urlparse
            "http://",
            "https://",
        ],
    )
    async def test_invalid_urls(self, invalid_url: str) -> None:
        """Test that invalid URLs fail validation."""
        args = ContainerRegistryValidatorArgs(
            url=invalid_url, type=ContainerRegistryType.DOCKER, project=None
        )
        validator = ContainerRegistryValidator(args)
        with pytest.raises(InvalidContainerRegistryURL, match=f"Invalid URL format: {invalid_url}"):
            validator.validate()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "registry_type, registry_url",
        [
            (ContainerRegistryType.HARBOR, "https://harbor.example.com"),
            (ContainerRegistryType.HARBOR2, "https://harbor2.example.com"),
        ],
    )
    async def test_harbor_project_validation_required(self, registry_type, registry_url) -> None:
        """Test that Harbor registries require project names."""
        args = ContainerRegistryValidatorArgs(url=registry_url, type=registry_type, project=None)
        validator = ContainerRegistryValidator(args)
        with pytest.raises(
            InvalidContainerRegistryProject, match="Project name is required for Harbor."
        ):
            validator.validate()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "project_name",
        [
            "",  # Empty string
            "a" * 256,  # Too long (256 characters)
        ],
    )
    async def test_harbor_project_validation_length(self, project_name) -> None:
        """Test Harbor project name length validation."""
        # Empty string (length 0)
        args = ContainerRegistryValidatorArgs(
            url="https://harbor.example.com",
            type=ContainerRegistryType.HARBOR,
            project=project_name,
        )
        validator = ContainerRegistryValidator(args)
        with pytest.raises(InvalidContainerRegistryProject, match="Invalid project name length."):
            validator.validate()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_project_name",
        [
            # Starting with special characters
            "-project",
            "_project",
            ".project",
            # Ending with special characters
            "project-",
            "project_",
            "project.",
            # Uppercase letters
            "Project",
            "PROJECT",
            "myProject",
            # Invalid characters
            "project@name",
            "project#name",
            "project name",
            "project!",
            # Double separators
            "project--name",
            "project__name",
            "project..name",
            "project.-name",
            "project_.name",
        ],
    )
    async def test_harbor_project_validation_format(self, invalid_project_name) -> None:
        """Test Harbor project name format validation."""

        args = ContainerRegistryValidatorArgs(
            url="https://harbor.example.com",
            type=ContainerRegistryType.HARBOR,
            project=invalid_project_name,
        )
        validator = ContainerRegistryValidator(args)
        with pytest.raises(InvalidContainerRegistryProject, match="Invalid project name format."):
            validator.validate()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "valid_project_name",
        [
            # Simple names
            "project",
            "myproject",
            "test",
            "p",
            # With numbers
            "project1",
            "project123",
            "123project",
            "1",
            # With allowed separators
            "my-project",
            "my_project",
            "my.project",
            "project-name-test",
            "project_name_test",
            "project.name.test",
            # Mixed separators
            "project-name_test",
            "project.name-test",
            "project_name.test",
            # Edge cases for length (1 and 255 characters)
            "a",
            "a" * 255,
        ],
    )
    async def test_harbor_project_validation_valid_names(self, valid_project_name) -> None:
        """Test that valid Harbor project names pass validation."""
        args = ContainerRegistryValidatorArgs(
            url="https://harbor.example.com",
            type=ContainerRegistryType.HARBOR,
            project=valid_project_name,
        )
        validator = ContainerRegistryValidator(args)
        # Should not raise any exception
        validator.validate()
