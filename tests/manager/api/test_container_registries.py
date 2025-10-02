import json

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
from ai.backend.manager.server import (
    database_ctx,
    hook_plugin_ctx,
    monitoring_ctx,
    redis_ctx,
)

FIXTURES_WITH_NOASSOC = [
    {
        "groups": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "name": "mock_group",
                "description": "",
                "is_active": True,
                "domain_name": "default",
                "resource_policy": "default",
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "type": "general",
            }
        ],
        "container_registries": [
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "url": "https://mock.registry.com",
                "type": "docker",
                "project": "mock_project",
                "registry_name": "mock_registry",
            }
        ],
    }
]

FIXTURES_WITH_ASSOC = [
    {
        **fixture,
        "association_container_registries_groups": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "group_id": "00000000-0000-0000-0000-000000000001",
                "registry_id": "00000000-0000-0000-0000-000000000002",
            }
        ],
    }
    for fixture in FIXTURES_WITH_NOASSOC
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_fixtures",
    FIXTURES_WITH_NOASSOC + FIXTURES_WITH_ASSOC,
    ids=["(No association)", "(With association)"],
)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "group_id": "00000000-0000-0000-0000-000000000001",
            "registry_id": "00000000-0000-0000-0000-000000000002",
        },
    ],
    ids=["Associate One group with one container registry"],
)
async def test_associate_container_registry_with_group(
    test_case,
    etcd_fixture,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    extra_fixtures,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    app, client = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
        ],
        [".container_registry", ".auth"],
    )

    group_id = test_case["group_id"]
    registry_id = test_case["registry_id"]

    url = f"/container-registries/{registry_id}"
    params = {"allowed_groups": {"add": [group_id]}}

    req_bytes = json.dumps(params).encode()
    headers = get_headers("PATCH", url, req_bytes)

    resp = await client.patch(url, data=req_bytes, headers=headers)
    association_exist = "association_container_registries_groups" in extra_fixtures

    if association_exist:
        assert resp.status == 400
    else:
        assert resp.status == 200


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_fixtures",
    FIXTURES_WITH_ASSOC + FIXTURES_WITH_NOASSOC,
    ids=["(With association)", "(No association)"],
)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "group_id": "00000000-0000-0000-0000-000000000001",
            "registry_id": "00000000-0000-0000-0000-000000000002",
        },
    ],
    ids=["Disassociate One group with one container registry"],
)
async def test_disassociate_container_registry_with_group(
    test_case,
    etcd_fixture,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    extra_fixtures,
    database_fixture,
    create_app_and_client,
    get_headers,
):
    app, client = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
            monitoring_ctx,
            hook_plugin_ctx,
            redis_ctx,
        ],
        [".container_registry", ".auth"],
    )

    group_id = test_case["group_id"]
    registry_id = test_case["registry_id"]

    url = f"/container-registries/{registry_id}"
    params = {"allowed_groups": {"remove": [group_id]}}

    req_bytes = json.dumps(params).encode()
    headers = get_headers("PATCH", url, req_bytes)

    resp = await client.patch(url, data=req_bytes, headers=headers)
    association_exist = "association_container_registries_groups" in extra_fixtures

    if association_exist:
        assert resp.status == 200
    else:
        assert resp.status == 404


class TestContainerRegistryValidator:
    def test_valid_urls(self) -> None:
        """Test that valid URLs pass validation."""
        valid_urls = [
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
        ]

        for url in valid_urls:
            args = ContainerRegistryValidatorArgs(
                url=url, type=ContainerRegistryType.DOCKER, project=None
            )
            validator = ContainerRegistryValidator(args)
            # Should not raise any exception
            validator.validate()

    def test_invalid_urls(self) -> None:
        """Test that invalid URLs fail validation."""
        invalid_urls = [
            # Empty or whitespace-only URLs
            "",
            "   ",
            # Malformed URLs that fail urlparse
            "http://",
            "https://",
        ]

        for url in invalid_urls:
            args = ContainerRegistryValidatorArgs(
                url=url, type=ContainerRegistryType.DOCKER, project=None
            )
            validator = ContainerRegistryValidator(args)
            with pytest.raises(InvalidContainerRegistryURL, match=f"Invalid URL format: {url}"):
                validator.validate()

    def test_harbor_project_validation_required(self) -> None:
        """Test that Harbor registries require project names."""
        for registry_type in [ContainerRegistryType.HARBOR, ContainerRegistryType.HARBOR2]:
            args = ContainerRegistryValidatorArgs(
                url="https://harbor.example.com", type=registry_type, project=None
            )
            validator = ContainerRegistryValidator(args)
            with pytest.raises(
                InvalidContainerRegistryProject, match="Project name is required for Harbor."
            ):
                validator.validate()

    def test_harbor_project_validation_length(self) -> None:
        """Test Harbor project name length validation."""
        # Empty string (length 0)
        args = ContainerRegistryValidatorArgs(
            url="https://harbor.example.com", type=ContainerRegistryType.HARBOR, project=""
        )
        validator = ContainerRegistryValidator(args)
        with pytest.raises(InvalidContainerRegistryProject, match="Invalid project name length."):
            validator.validate()

        # Too long (256 characters)
        long_project = "a" * 256
        args = ContainerRegistryValidatorArgs(
            url="https://harbor.example.com",
            type=ContainerRegistryType.HARBOR,
            project=long_project,
        )
        validator = ContainerRegistryValidator(args)
        with pytest.raises(InvalidContainerRegistryProject, match="Invalid project name length."):
            validator.validate()

    def test_harbor_project_validation_format(self) -> None:
        """Test Harbor project name format validation."""
        invalid_projects = [
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
        ]

        for project in invalid_projects:
            args = ContainerRegistryValidatorArgs(
                url="https://harbor.example.com", type=ContainerRegistryType.HARBOR, project=project
            )
            validator = ContainerRegistryValidator(args)
            with pytest.raises(
                InvalidContainerRegistryProject, match="Invalid project name format."
            ):
                validator.validate()

    def test_harbor_project_validation_valid_names(self) -> None:
        """Test that valid Harbor project names pass validation."""
        valid_projects = [
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
        ]

        for project in valid_projects:
            args = ContainerRegistryValidatorArgs(
                url="https://harbor.example.com", type=ContainerRegistryType.HARBOR, project=project
            )
            validator = ContainerRegistryValidator(args)
            # Should not raise any exception
            validator.validate()
