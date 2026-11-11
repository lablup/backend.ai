from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.repositories.auth.repository import AuthRepository
from ai.backend.manager.repositories.user_resource_policy.repository import (
    UserResourcePolicyRepository,
)
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.auth.actions.generate_ssh_keypair import (
    GenerateSSHKeypairAction,
)
from ai.backend.manager.services.auth.actions.get_ssh_keypair import (
    GetSSHKeypairAction,
)
from ai.backend.manager.services.auth.actions.upload_ssh_keypair import (
    UploadSSHKeypairAction,
)
from ai.backend.manager.services.auth.service import AuthService


@pytest.fixture
def mock_auth_repository() -> AsyncMock:
    return AsyncMock(spec=AuthRepository)


@pytest.fixture
def auth_service(
    mock_hook_plugin_ctx: AsyncMock,
    mock_auth_repository: AsyncMock,
    mock_config_provider: AsyncMock,
    mock_user_repository: AsyncMock,
    mock_group_repository: AsyncMock,
    mock_client_ip_masking_repository: AsyncMock,
) -> AuthService:
    return AuthService(
        hook_plugin_ctx=mock_hook_plugin_ctx,
        auth_repository=mock_auth_repository,
        config_provider=mock_config_provider,
        valkey_session_client=AsyncMock(),
        user_resource_policy_repository=AsyncMock(spec=UserResourcePolicyRepository),
        user_repository=mock_user_repository,
        group_repository=mock_group_repository,
        client_ip_masking_repository=mock_client_ip_masking_repository,
        key_provider_pool=KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )


# Test Get SSH Keypair
async def test_get_ssh_keypair_existing_key(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
) -> None:
    """Test getting existing SSH public key"""
    action = GetSSHKeypairAction(
        user_id=UserID(UUID("12345678-1234-5678-1234-567812345678")),
        access_key="AKIA1234567890ABCDEF",
    )

    mock_auth_repository.get_ssh_public_key.return_value = (
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..."
    )

    result = await auth_service.get_ssh_keypair(action)

    assert result.public_key == "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..."
    mock_auth_repository.get_ssh_public_key.assert_called_once_with(action.access_key)


async def test_get_ssh_keypair_nonexistent_key(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
) -> None:
    """Test getting non-existing SSH public key returns empty string"""
    action = GetSSHKeypairAction(
        user_id=UserID(UUID("12345678-1234-5678-1234-567812345678")),
        access_key="AKIANONEXISTENT",
    )

    mock_auth_repository.get_ssh_public_key.return_value = None

    result = await auth_service.get_ssh_keypair(action)

    assert result.public_key == ""
    mock_auth_repository.get_ssh_public_key.assert_called_once_with(action.access_key)


# Test Generate SSH Keypair
async def test_generate_ssh_keypair(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
) -> None:
    """Test SSH keypair generation"""
    action = GenerateSSHKeypairAction(
        user_id=UserID(UUID("12345678-1234-5678-1234-567812345678")),
        access_key="AKIA1234567890ABCDEF",
    )

    # Mock the keypair generation
    mock_pubkey = "ssh-rsa AAAAB3NzaC1yc2EGENERATED..."
    mock_privkey = "-----BEGIN RSA PRIVATE KEY-----\nGENERATED...\n-----END RSA PRIVATE KEY-----"

    with patch(
        "ai.backend.manager.services.auth.service.generate_ssh_keypair",
        return_value=(mock_pubkey, mock_privkey),
    ):
        result = await auth_service.generate_ssh_keypair(action)

    # Verify repository was called with generated keys
    mock_auth_repository.update_ssh_keypair.assert_called_once_with(
        "AKIA1234567890ABCDEF",
        mock_pubkey,
        mock_privkey,
    )

    assert result.ssh_keypair.ssh_public_key == mock_pubkey
    assert result.ssh_keypair.ssh_private_key == mock_privkey


# Test Upload SSH Keypair
async def test_upload_ssh_keypair_replaces_only_the_public_key(
    auth_service: AuthService,
    mock_auth_repository: AsyncMock,
) -> None:
    """Test uploading an SSH public key leaves the stored private key alone"""
    action = UploadSSHKeypairAction(
        user_id=UserID(UUID("12345678-1234-5678-1234-567812345678")),
        access_key="AKIA1234567890ABCDEF",
        public_key="ssh-rsa AAAAB3NzaC1yc2EUPLOADED...",
    )

    result = await auth_service.upload_ssh_keypair(action)

    mock_auth_repository.update_ssh_public_key.assert_called_once_with(
        action.access_key,
        action.public_key,
    )
    mock_auth_repository.update_ssh_keypair.assert_not_called()
    assert result.public_key == action.public_key
