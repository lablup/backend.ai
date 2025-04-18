from http import HTTPStatus

import pytest

from ai.backend.client.config import get_config
from ai.backend.client.session import Session


@pytest.mark.asyncio
async def test_vfolder_mkdir() -> None:
    config = get_config()
    with Session(config=config) as sess:
        vfolder = sess.VFolder("fake-vfolder-name")
        resp = vfolder.mkdir("fake-dir")
        assert resp.status_code == HTTPStatus.OK
        assert resp.get("success") is not None
        assert resp.get("failure") is not None
        assert resp.get("results") is None
