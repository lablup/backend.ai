import uuid

from ai.backend.client.cli.session.execute import prepare_mount_arg
from ai.backend.common.types import MountPermission, MountTypes


def test_vfolder_mount() -> None:
    # given
    mount = [
        "type=bind,source=/colon\\:path/test,target=/data",
        "type=bind,source=/usr/abcd,target=/home/work/zxcv,perm=ro",
        "type=bind,source=/usr/lorem,target=/home/work/ipsum,permission=ro",
        "source=/src/hello,target=/trg/hello,perm=rw",
    ]

    # when
    mount, mount_map, mount_options, mount_ids, mount_id_map = prepare_mount_arg(mount)

    # then
    assert set(mount) == {"/colon:path/test", "/usr/abcd", "/usr/lorem", "/src/hello"}
    assert mount_map == {
        "/colon:path/test": "/data",
        "/usr/abcd": "/home/work/zxcv",
        "/usr/lorem": "/home/work/ipsum",
        "/src/hello": "/trg/hello",
    }
    assert mount_options == {
        "/colon:path/test": {
            "type": MountTypes.BIND,
            "permission": None,
        },
        "/usr/abcd": {
            "type": MountTypes.BIND,
            "permission": MountPermission.READ_ONLY,
        },
        "/usr/lorem": {
            "type": MountTypes.BIND,
            "permission": MountPermission.READ_ONLY,
        },
        "/src/hello": {
            "type": MountTypes.BIND,
            "permission": MountPermission.READ_WRITE,
        },
    }


def test_vfolder_mount_uuid_routes_to_mount_ids() -> None:
    # given
    # UUIDs that start with a letter — the MountExpression parser's
    # underlying lark grammar requires a CNAME (letter/underscore) at the
    # start of a token, so digit-starting UUIDs fail to parse upstream
    # regardless of this fix.
    vfid_a = "d2b0f974-80d0-4988-8e99-0347c2f45965"
    vfid_b = "abcd1234-2222-3333-4444-555555555555"
    mount = [
        # plain UUID (no target)
        vfid_a,
        # UUID with target
        f"{vfid_b}:/home/work/data",
        # mixed: a name-keyed entry stays in the name bucket
        "vf-name-only:/home/work/keep",
    ]

    # when
    names, name_map, name_opts, ids, id_map = prepare_mount_arg(mount)

    # then
    assert set(ids) == {uuid.UUID(vfid_a), uuid.UUID(vfid_b)}
    assert id_map == {uuid.UUID(vfid_b): "/home/work/data"}
    assert names == ["vf-name-only"]
    assert name_map == {"vf-name-only": "/home/work/keep"}
    # UUID entries do not pollute the name-keyed options dict
    assert set(name_opts) == {"vf-name-only"}


def test_vfolder_mount_without_target() -> None:
    # given
    mount = [
        "type=volume,source=vf-dd244f7f,perm=ro",
    ]

    # when
    mount, mount_map, mount_options, mount_ids, mount_id_map = prepare_mount_arg(mount)

    # then
    assert set(mount) == {"vf-dd244f7f"}
    assert mount_map == {}
    assert mount_options == {
        "vf-dd244f7f": {
            "type": MountTypes.VOLUME,
            "permission": MountPermission.READ_ONLY,
        },
    }


def test_vfolder_mount__edge_cases_with() -> None:
    # given
    mount = [
        "type=bind,source=vf-abc\\,zxc,target=/home/work",  # source with a comma
        "type=bind,source=vf-abc\\=zxc,target=/home/work",  # source with an equals sign
    ]

    # when
    mount_unescaped, *_ = prepare_mount_arg(mount, escape=False)

    # then
    assert set(mount_unescaped) == {"vf-abc\\,zxc", "vf-abc\\=zxc"}

    # when
    mount_escaped, *_ = prepare_mount_arg(mount, escape=True)

    # then
    assert set(mount_escaped) == {"vf-abc,zxc", "vf-abc=zxc"}
