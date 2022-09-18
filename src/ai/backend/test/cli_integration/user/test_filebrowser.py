from unittest import mock

import pytest
from aioresponses import aioresponses

from ai.backend.client.config import API_VERSION
from ai.backend.client.session import Session
from ai.backend.client.test_utils import AsyncMock


def build_url(config, path: str):
    base_url = config.endpoint.path.rstrip("/")
    query_path = path.lstrip("/") if len(path) > 0 else ""
    path = "{0}/{1}".format(base_url, query_path)
    canonical_url = config.endpoint.with_path(path)
    return canonical_url


@pytest.fixture(scope="module", autouse=True)
def api_version():
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield


def test_create_vfolder():
    host = "local:volume1"
    vfolders = ["mydata1"]
    with Session() as session, aioresponses() as m:
        payload = {
            "host": host,
            "vfolders": vfolders,
            "status": "ok",
            "addr": "127.0.0.1",
            "container_id": "00000000",
        }
        m.post(
            build_url(session.config, "/storage/filebrowser/create"),
            status=201,
            payload=payload,
        )
        resp = session.FileBrowser.create_or_update_browser(host, vfolders)
        assert resp == payload


def destroy_browser():
    container_id = "0000000"
    with Session() as session, aioresponses() as m:
        payload = {
            "container_id": container_id,
            "status": "ok",
        }
        m.delete(
            build_url(session.config, "/storage/filebrowser/destroy"),
            status=201,
            payload=payload,
        )
        resp = session.FileBrowser.destroy(container_id)
        assert resp == payload
