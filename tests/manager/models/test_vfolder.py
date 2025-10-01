from pathlib import PurePosixPath
from uuid import UUID

import pytest

from ai.backend.common.metrics.metric import GraphQLMetricObserver
from ai.backend.common.types import VFolderMount
from ai.backend.manager.models.gql import GraphQueryContext
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.vfolder import (
    MountPermission,
    VFolderID,
    VirtualFolder,
    is_mount_duplicate,
)
from ai.backend.manager.server import (
    database_ctx,
)


def get_graphquery_context(database_engine: ExtendedAsyncSAEngine) -> GraphQueryContext:
    return GraphQueryContext(
        schema=None,  # type: ignore
        dataloader_manager=None,  # type: ignore
        config_provider=None,  # type: ignore
        etcd=None,  # type: ignore
        user={"domain": "default", "role": "superadmin"},
        access_key="AKIAIOSFODNN7EXAMPLE",
        db=database_engine,  # type: ignore
        valkey_stat=None,  # type: ignore
        valkey_image=None,  # type: ignore
        valkey_live=None,  # type: ignore
        valkey_schedule=None,  # type: ignore
        manager_status=None,  # type: ignore
        known_slot_types=None,  # type: ignore
        background_task_manager=None,  # type: ignore
        storage_manager=None,  # type: ignore
        registry=None,  # type: ignore
        idle_checker_host=None,  # type: ignore
        network_plugin_ctx=None,  # type: ignore
        services_ctx=None,  # type: ignore
        metric_observer=GraphQLMetricObserver.instance(),
        processors=None,  # type: ignore
        scheduler_repository=None,  # type: ignore
        user_repository=None,  # type: ignore
        agent_repository=None,  # type: ignore
    )


FIXTURES = [
    {
        "users": [
            {
                "uuid": "00000000-0000-0000-0000-000000000000",
                "username": "mock_user",
                "email": "",
                "password": "",
                "need_password_change": False,
                "full_name": "",
                "description": "",
                "status": "active",
                "status_info": "admin-requested",
                "domain_name": "default",
                "resource_policy": "default",
                "role": "superadmin",
            }
        ],
        "groups": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "name": "mock_group",
                "description": "",
                "is_active": True,
                "domain_name": "default",
                "resource_policy": "default",
                "total_resource_slots": {},
                "allowed_vfolder_hosts": {},
                "type": "general",
            },
        ],
        "vfolders": [
            {
                "id": "00000000-0000-0000-0000-000000000001",
                "host": "mock",
                "domain_name": "default",
                "name": "mock_vfolder_1",
                "quota_scope_id": "user:00000000-0000-0000-0000-000000000000",
                "usage_mode": "general",
                "permission": "rw",
                "ownership_type": "user",
                "status": "ready",
                "cloneable": False,
                "max_files": 0,
                "num_files": 0,
                "user": "00000000-0000-0000-0000-000000000000",
                "group": None,
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "host": "mock",
                "domain_name": "default",
                "name": "mock_vfolder_2",
                "quota_scope_id": "user:00000000-0000-0000-0000-000000000000",
                "usage_mode": "general",
                "permission": "rw",
                "ownership_type": "user",
                "status": "ready",
                "cloneable": False,
                "max_files": 0,
                "num_files": 0,
                "user": "00000000-0000-0000-0000-000000000000",
                "group": None,
            },
            {
                "id": "00000000-0000-0000-0000-000000000003",
                "host": "mock",
                "domain_name": "default",
                "name": "mock_vfolder_3",
                "quota_scope_id": "project:00000000-0000-0000-0000-000000000000",
                "usage_mode": "general",
                "permission": "rw",
                "ownership_type": "group",
                "status": "ready",
                "cloneable": False,
                "max_files": 0,
                "num_files": 0,
                "user": None,
                "group": "00000000-0000-0000-0000-000000000000",
            },
        ],
    }
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "extra_fixtures",
    FIXTURES,
)
@pytest.mark.parametrize(
    "test_case",
    [
        {
            "vfolder_ids": [UUID("00000000-0000-0000-0000-000000000001")],
            "user_id": None,
            "group_id": None,
            "domain_name": None,
            "expected_result": [UUID("00000000-0000-0000-0000-000000000001")],
        },
        {
            "vfolder_ids": [
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
            ],
            "user_id": None,
            "group_id": None,
            "domain_name": None,
            "expected_result": [
                UUID("00000000-0000-0000-0000-000000000001"),
                UUID("00000000-0000-0000-0000-000000000002"),
            ],
        },
        {
            "vfolder_ids": [UUID("00000000-0000-0000-0000-000000000001")],
            "user_id": UUID("00000000-0000-0000-0000-000000000000"),
            "group_id": None,
            "domain_name": None,
            "expected_result": [UUID("00000000-0000-0000-0000-000000000001")],
        },
        {
            "vfolder_ids": [UUID("00000000-0000-0000-0000-000000000001")],
            "user_id": UUID("00000000-0000-0000-0000-000000000000"),
            "group_id": None,
            "domain_name": "default",
            "expected_result": [UUID("00000000-0000-0000-0000-000000000001")],
        },
        {
            "vfolder_ids": [UUID("00000000-0000-0000-0000-000000000001")],
            "user_id": UUID("00000000-0000-0000-0000-000000000000"),
            "group_id": None,
            "domain_name": "INVALID",
            "expected_result": [None],
        },
        {
            "vfolder_ids": [UUID("00000000-0000-0000-0000-000000000003")],
            "user_id": None,
            "group_id": UUID("00000000-0000-0000-0000-000000000000"),
            "domain_name": None,
            "expected_result": [UUID("00000000-0000-0000-0000-000000000003")],
        },
    ],
    ids=[
        "Batchload a vfolder by id",
        "Batchload multiple vfolders by ids",
        "Batchload a vfolder by user_id",
        "Batchload a vfolder by user_id and domain_name",
        "Batchload a vfolder by user_id and invalid domain_name",
        "Batchload a vfolder by group_id",
    ],
)
async def test_batch_load_by_id(
    test_case,
    mock_etcd_ctx,
    mock_config_provider_ctx,
    database_fixture,
    create_app_and_client,
):
    test_app, _ = await create_app_and_client(
        [
            mock_etcd_ctx,
            mock_config_provider_ctx,
            database_ctx,
        ],
        [],
    )

    root_ctx = test_app["_root.context"]
    context = get_graphquery_context(root_ctx.db)

    vfolder_ids = test_case["vfolder_ids"]
    user_id = test_case["user_id"]
    group_id = test_case["group_id"]
    domain_name = test_case["domain_name"]
    expected_result = test_case["expected_result"]

    result = await VirtualFolder.batch_load_by_id(
        context,
        vfolder_ids,
        user_id=user_id,
        group_id=group_id,
        domain_name=domain_name,
    )

    assert len(result) == len(expected_result)
    for res, expected_id in zip(result, expected_result):
        if expected_id is None:
            assert res is None
        else:
            assert res.id == expected_id


@pytest.mark.parametrize(
    "vf_id_subpath_pair",
    [
        (VFolderID(None, UUID("00000000-0000-0000-0000-000000000001")), PurePosixPath(".mytest")),
    ],
)
@pytest.mark.parametrize(
    "vfmounts",
    [
        [
            VFolderMount.from_json({
                "name": "vfolder_1",
                "vfid": UUID("00000000-0000-0000-0000-000000000001"),
                "vfsubpath": PurePosixPath(".mytest"),
                "host_path": PurePosixPath("."),
                "kernel_path": PurePosixPath("."),
                "mount_perm": MountPermission.READ_WRITE,
            }),
        ],
    ],
)
def test_mounts_duplicate(vf_id_subpath_pair, vfmounts) -> None:
    assert is_mount_duplicate(vf_id_subpath_pair[0], vf_id_subpath_pair[1], vfmounts)


@pytest.mark.parametrize(
    "vf_id_subpath_pair",
    [
        (VFolderID(None, UUID("00000000-0000-0000-0000-000000000001")), PurePosixPath(".mytest")),
        (VFolderID(None, UUID("00000000-0000-0000-0000-000000000001")), PurePosixPath("subpath1")),
    ],
)
@pytest.mark.parametrize(
    "vfmounts",
    [
        [
            VFolderMount.from_json({
                "name": "vfolder_1",
                "vfid": UUID("00000000-0000-0000-0000-000000000001"),
                "vfsubpath": PurePosixPath(".pipeline"),
                "host_path": PurePosixPath("."),
                "kernel_path": PurePosixPath("."),
                "mount_perm": MountPermission.READ_WRITE,
            }),
        ],
        [
            VFolderMount.from_json({
                "name": "vfolder_1",
                "vfid": UUID("00000000-0000-0000-0000-000000000002"),
                "vfsubpath": PurePosixPath("subpath1"),
                "host_path": PurePosixPath("."),
                "kernel_path": PurePosixPath("."),
                "mount_perm": MountPermission.READ_WRITE,
            }),
        ],
    ],
)
def test_mounts_not_duplicate(vf_id_subpath_pair, vfmounts) -> None:
    assert not is_mount_duplicate(vf_id_subpath_pair[0], vf_id_subpath_pair[1], vfmounts)


@pytest.mark.parametrize(
    "vf_id_subpath_pair",
    [
        (
            VFolderID(None, UUID("00000000-0000-0000-0000-000000000001")),
            PurePosixPath(".pipeline/vfroot"),
        ),
    ],
)
@pytest.mark.parametrize(
    "vfmounts",
    [
        [
            VFolderMount.from_json({
                "name": "vfolder_1",
                "vfid": UUID("00000000-0000-0000-0000-000000000001"),
                "vfsubpath": PurePosixPath(".pipeline"),
                "host_path": PurePosixPath("."),
                "kernel_path": PurePosixPath("."),
                "mount_perm": MountPermission.READ_WRITE,
            }),
        ]
    ],
)
def test_mounts_inclusion_duplicate(vf_id_subpath_pair, vfmounts) -> None:
    assert is_mount_duplicate(vf_id_subpath_pair[0], vf_id_subpath_pair[1], vfmounts)
