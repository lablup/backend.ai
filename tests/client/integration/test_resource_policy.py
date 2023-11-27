import uuid

import pytest

from ai.backend.client.config import get_config
from ai.backend.client.exceptions import BackendAPIError
from ai.backend.client.session import Session

# module-level marker
pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_manipulate_resource_policy(self):
    access_key = get_config().access_key
    rpname = "testrp-" + uuid.uuid4().hex
    with Session() as sess:
        try:
            rp = sess.ResourcePolicy(access_key)
            assert rp.info(rpname) is None
            rps = sess.ResourcePolicy.list()
            original_count = len(rps)

            # Create resource policy
            sess.ResourcePolicy.create(
                name=rpname,
                default_for_unspecified="LIMITED",
                total_resource_slots="{}",
                max_concurrent_sessions=1,
                max_containers_per_session=1,
                idle_timeout=1,
                allowed_vfolder_hosts=["local"],
            )
            rps = sess.ResourcePolicy.list()
            assert len(rps) == original_count + 1
            info = rp.info(rpname)
            assert info["name"] == rpname
            assert info["total_resource_slots"] == "{}"
            assert info["max_concurrent_sessions"] == 1
            assert info["idle_timeout"] == 1

            # Update resource policy
            sess.ResourcePolicy.update(
                name=rpname,
                default_for_unspecified="LIMITED",
                total_resource_slots='{"cpu": "count"}',
                max_concurrent_sessions=2,
                max_containers_per_session=2,
                idle_timeout=2,
                allowed_vfolder_hosts=["local"],
            )
            rps = sess.ResourcePolicy.list()
            assert len(rps) == original_count + 1
            info = rp.info(rpname)
            assert info["name"] == rpname
            assert info["total_resource_slots"] == '{"cpu": "count"}'
            assert info["max_concurrent_sessions"] == 2
            assert info["idle_timeout"] == 2

            # Delete ResourcePolicy
            sess.ResourcePolicy.delete(rpname)
            rps = sess.ResourcePolicy.list()
            assert len(rps) == original_count
        except Exception:
            sess.ResourcePolicy.delete(rpname)
            raise


@pytest.mark.asyncio
async def test_user_cannot_create_resource_policy(self, userconfig):
    rpname = "testrp-" + uuid.uuid4().hex
    with Session() as sess:
        with pytest.raises(BackendAPIError):
            sess.ResourcePolicy.create(
                name=rpname,
                default_for_unspecified="LIMITED",
                total_resource_slots="{}",
                max_concurrent_sessions=1,
                max_containers_per_session=1,
                idle_timeout=1,
                allowed_vfolder_hosts=["local"],
            )
