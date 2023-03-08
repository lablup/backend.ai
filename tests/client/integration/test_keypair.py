import uuid

import pytest

from ai.backend.client.config import get_config
from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import Session

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_keypair_manipulation_operations():
    email = "testion" + uuid.uuid4().hex + "@test.mars"
    access_key = None
    with Session() as sess:
        try:
            # Create keypair
            result = sess.KeyPair.create(
                user_id=email,
                is_active=True,
                is_admin=False,
                resource_policy="default",
                rate_limit=1,
            )
            access_key = result["keypair"]["access_key"]
            keypairs = sess.KeyPair.list(user_id=email)
            assert len(keypairs) == 1
            assert keypairs[0]["access_key"] == access_key
            assert keypairs[0]["is_active"]
            assert not keypairs[0]["is_admin"]

            # Update keypair
            sess.KeyPair.update(access_key, is_active=False)
            keypairs = sess.KeyPair.list(user_id=email)
            assert not keypairs[0]["is_active"]

            # Activate keypair
            sess.KeyPair.activate(access_key)
            keypairs = sess.KeyPair.list(user_id=email)
            assert keypairs[0]["is_active"]

            # Deactivate keypair
            sess.KeyPair.deactivate(access_key)
            keypairs = sess.KeyPair.list(user_id=email)
            assert not keypairs[0]["is_active"]

            # Delete Keypair
            sess.KeyPair.delete(access_key)
            keypairs = sess.KeyPair.list(user_id=email)
            assert len(keypairs) == 0
        except Exception:
            if access_key:
                sess.KeyPair.delete(access_key)
            raise


@pytest.mark.asyncio
async def test_user_cannot_create_keypair(userconfig):
    email = "testion" + uuid.uuid4().hex + "@test.mars"
    with Session() as sess:
        with pytest.raises(BackendAPIError):
            sess.KeyPair.create(
                user_id=email,
                is_active=True,
                is_admin=False,
                resource_policy="default",
                rate_limit=1,
            )


@pytest.mark.asyncio
async def test_keypair_info():
    current_config = get_config()
    with Session() as sess:
        result = sess.KeyPair(current_config.access_key).info()
    assert result["access_key"] == current_config.access_key
    assert result["secret_key"] == current_config.secret_key
