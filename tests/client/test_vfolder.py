from collections.abc import Iterator
from http import HTTPStatus
from typing import Mapping, Optional, Union
from unittest import mock
from uuid import UUID

import pytest
from aioresponses import aioresponses
from yarl import URL

from ai.backend.client.config import API_VERSION, APIConfig
from ai.backend.client.session import Session
from ai.backend.testutils.mock import AsyncMock


def build_url(
    config: APIConfig, path: str, params: Optional[Mapping[str, Union[str, int]]] = None
) -> URL:
    base_url = config.endpoint.path.rstrip("/")
    query_path = path.lstrip("/") if len(path) > 0 else ""
    path = "{0}/{1}".format(base_url, query_path)
    canonical_url = config.endpoint.with_path(path)
    if params:
        canonical_url = canonical_url.with_query(params)
    return canonical_url


@pytest.fixture(scope="module", autouse=True)
def api_version() -> Iterator[None]:
    mock_nego_func = AsyncMock()
    mock_nego_func.return_value = API_VERSION
    with mock.patch("ai.backend.client.session._negotiate_api_version", mock_nego_func):
        yield


def test_create_vfolder() -> None:
    with Session() as session, aioresponses() as m:
        payload = {
            "id": "fake-vfolder-id",
            "name": "fake-vfolder-name",
            "host": "local",
        }
        m.post(build_url(session.config, "/folders"), status=HTTPStatus.CREATED, payload=payload)
        resp = session.VFolder.create("fake-vfolder-name")
        assert resp == payload


def test_create_vfolder_in_other_host() -> None:
    with Session() as session, aioresponses() as m:
        payload = {
            "id": "fake-vfolder-id",
            "name": "fake-vfolder-name",
            "host": "fake-vfolder-host",
        }
        m.post(build_url(session.config, "/folders"), status=HTTPStatus.CREATED, payload=payload)
        resp = session.VFolder.create("fake-vfolder-name", "fake-vfolder-host")
        assert resp == payload


def test_list_vfolders() -> None:
    with Session() as session, aioresponses() as m:
        payload = [
            {
                "name": "fake-vfolder1",
                "id": "fake-vfolder1-id",
                "host": "fake-vfolder1-host",
                "is_owner": True,
                "permissions": "wd",
            },
            {
                "name": "fake-vfolder2",
                "id": "fake-vfolder2-id",
                "host": "fake-vfolder2-host",
                "is_owner": True,
                "permissions": "wd",
            },
        ]
        m.get(build_url(session.config, "/folders"), status=HTTPStatus.OK, payload=payload)
        resp = session.VFolder.list()
        assert resp == payload


def test_delete_vfolder() -> None:
    with Session() as session, aioresponses() as m:
        vfolder_name = "fake-vfolder-name"
        source_vfolder_uuid: UUID = UUID("c59395cd-ac91-4cd3-a1b0-3d2568aa2d04")
        m.get(
            build_url(session.config, "/folders/_/id"),
            status=HTTPStatus.OK,
            payload={"id": source_vfolder_uuid.hex},
        )
        m.delete(build_url(session.config, "/folders"), status=HTTPStatus.NO_CONTENT)
        resp = session.VFolder(vfolder_name).delete()
        assert resp == {}


def test_vfolder_get_info() -> None:
    with Session() as session, aioresponses() as m:
        vfolder_name = "fake-vfolder-name"
        payload = {
            "name": vfolder_name,
            "id": "fake-vfolder-id",
            "host": "fake-vfolder-host",
            "numFiles": 5,
            "created": "2018-06-02 09:04:15.585917+00:00",
            "is_owner": True,
            "permission": "wd",
        }
        source_vfolder_uuid: UUID = UUID("c59395cd-ac91-4cd3-a1b0-3d2568aa2d04")
        m.get(
            build_url(session.config, "/folders/_/id"),
            status=HTTPStatus.OK,
            payload={"id": source_vfolder_uuid.hex},
        )
        m.get(
            build_url(session.config, "/folders/{}".format(source_vfolder_uuid.hex)),
            status=HTTPStatus.OK,
            payload=payload,
        )
        resp = session.VFolder(vfolder_name).info()
        assert resp == payload


def test_vfolder_delete_files() -> None:
    with Session() as session, aioresponses() as m:
        vfolder_name = "fake-vfolder-name"
        files = ["fake-file1", "fake-file2"]
        source_vfolder_uuid: UUID = UUID("c59395cd-ac91-4cd3-a1b0-3d2568aa2d04")
        m.get(
            build_url(session.config, "/folders/_/id"),
            status=HTTPStatus.OK,
            payload={"id": source_vfolder_uuid.hex},
        )
        m.delete(
            build_url(session.config, "/folders/{}/delete-files".format(source_vfolder_uuid.hex)),
            status=HTTPStatus.OK,
            payload={},
        )
        resp = session.VFolder(vfolder_name).delete_files(files)
        assert resp == "{}"


def test_vfolder_list_files() -> None:
    with Session() as session, aioresponses() as m:
        vfolder_name = "fake-vfolder-name"
        payload = {
            "files": [
                {
                    "mode": "-rw-r--r--",
                    "size": 4751244,
                    "ctime": 1528277299.2744732,
                    "mtime": 1528277299.2744732,
                    "atime": 1528277300.7658687,
                    "filename": "bigtxt.txt",
                },
                {
                    "mode": "-rw-r--r--",
                    "size": 200000,
                    "ctime": 1528333257.6576185,
                    "mtime": 1528288069.625786,
                    "atime": 1528332829.692922,
                    "filename": "200000",
                },
            ],
            "folder_path": "/mnt/local/1f6bd27fde1248cabfb50306ea83fc0a",
        }
        source_vfolder_uuid: UUID = UUID("c59395cd-ac91-4cd3-a1b0-3d2568aa2d04")
        m.get(
            build_url(session.config, "/folders/_/id"),
            status=HTTPStatus.OK,
            payload={"id": source_vfolder_uuid.hex},
        )
        m.get(
            build_url(
                session.config,
                "/folders/{}/files".format(source_vfolder_uuid.hex),
                params={"path": "."},
            ),
            status=HTTPStatus.OK,
            payload=payload,
        )
        resp = session.VFolder(vfolder_name).list_files(".")
        assert resp == payload


def test_vfolder_invite() -> None:
    with Session() as session, aioresponses() as m:
        vfolder_name = "fake-vfolder-name"
        user_ids = ["user1@lablup.com", "user2@lablup.com"]
        payload = {"invited_ids": user_ids}
        source_vfolder_uuid: UUID = UUID("c59395cd-ac91-4cd3-a1b0-3d2568aa2d04")
        m.get(
            build_url(session.config, "/folders/_/id"),
            status=HTTPStatus.OK,
            payload={"id": source_vfolder_uuid.hex},
        )
        m.post(
            build_url(session.config, "/folders/{}/invite".format(source_vfolder_uuid.hex)),
            status=HTTPStatus.CREATED,
            payload=payload,
        )
        resp = session.VFolder(vfolder_name).invite("rw", user_ids)
        assert resp == payload


def test_vfolder_invitations() -> None:
    with Session() as session, aioresponses() as m:
        payload = {
            "invitations": [
                {
                    "id": "fake-invitation-id",
                    "inviter": "inviter@lablup.com",
                    "perm": "ro",
                    "vfolder_id": "fake-vfolder-id",
                },
            ],
        }
        m.get(
            build_url(session.config, "/folders/invitations/list"),
            status=HTTPStatus.OK,
            payload=payload,
        )
        resp = session.VFolder.invitations()
        assert resp == payload


def test_vfolder_accept_invitation() -> None:
    with Session() as session, aioresponses() as m:
        payload = {
            "msg": "User invitee@lablup.com now can access vfolder fake-vfolder-id",
        }
        m.post(
            build_url(session.config, "/folders/invitations/accept"),
            status=HTTPStatus.OK,
            payload=payload,
        )
        resp = session.VFolder.accept_invitation("inv-id")
        assert resp == payload


def test_vfolder_delete_invitation() -> None:
    with Session() as session, aioresponses() as m:
        payload = {"msg": "Vfolder invitation is deleted: fake-inv-id."}
        m.delete(
            build_url(session.config, "/folders/invitations/delete"),
            status=HTTPStatus.OK,
            payload=payload,
        )
        resp = session.VFolder.delete_invitation("inv-id")
        assert resp == payload


def test_vfolder_clone() -> None:
    with Session() as session, aioresponses() as m:
        source_vfolder_name = "fake-source-vfolder-name"
        target_vfolder_name = "fake-target-vfolder-name"
        payload = {
            "target_name": target_vfolder_name,
            "target_host": "local",
            "permission": "rw",
            "usage_mode": "general",
        }
        source_vfolder_uuid: UUID = UUID("c59395cd-ac91-4cd3-a1b0-3d2568aa2d04")
        m.get(
            build_url(session.config, "/folders/_/id"),
            status=HTTPStatus.OK,
            payload={"id": source_vfolder_uuid.hex},
        )
        m.post(
            build_url(session.config, "/folders/{}/clone".format(source_vfolder_uuid.hex)),
            status=HTTPStatus.CREATED,
            payload=payload,
        )
        resp = session.VFolder(source_vfolder_name).clone(target_vfolder_name)
        assert resp == payload


def test_vfolder_force_delete() -> None:
    with Session() as session, aioresponses() as m:
        vfolder_uuid = UUID("c59395cd-ac91-4cd3-a1b0-3d2568aa2d04")
        m.get(
            build_url(session.config, "/folders/_/id"),
            status=HTTPStatus.OK,
            payload={"id": vfolder_uuid.hex},
        )
        m.delete(
            build_url(session.config, "/folders/{}/force".format(vfolder_uuid.hex)),
            status=HTTPStatus.NO_CONTENT,
            payload={},
        )
        resp = session.VFolder("", id=vfolder_uuid).force_delete()
    assert resp == {}
