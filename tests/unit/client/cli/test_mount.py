from ai.backend.client.cli.session.execute import prepare_mount_arg
from ai.backend.common.types import MountPermission, MountTypes


def test_vfolder_mount():
    # given
    mount = [
        "type=bind,source=/colon\\:path/test,target=/data",
        "type=bind,source=/usr/abcd,target=/home/work/zxcv,perm=ro",
        "type=bind,source=/usr/lorem,target=/home/work/ipsum,permission=ro",
        "source=/src/hello,target=/trg/hello,perm=rw",
    ]

    # when
    mount, mount_map, mount_options = prepare_mount_arg(mount)

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


def test_vfolder_mount_without_target():
    # given
    mount = [
        "type=volume,source=vf-dd244f7f,perm=ro",
    ]

    # when
    mount, mount_map, mount_options = prepare_mount_arg(mount)

    # then
    assert set(mount) == {"vf-dd244f7f"}
    assert mount_map == {}
    assert mount_options == {
        "vf-dd244f7f": {
            "type": MountTypes.VOLUME,
            "permission": MountPermission.READ_ONLY,
        },
    }


def test_vfolder_mount__edge_cases_with():
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
