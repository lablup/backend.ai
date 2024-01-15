from ai.backend.cli.types import MountType
from ai.backend.client.cli.session.execute import prepare_mount_arg, prepare_mount_arg_v2


def test_vfolder_mount_simple():
    # given
    mount = [
        "vf-5194d5d8",
        "vf-70b99ea5=abcd",
        "vf-cd6c0b91:qwer",
        "vf-db50b713/subpath:/lorem/ipsum/dolor",
    ]

    # when
    mount, mount_map = prepare_mount_arg(mount)

    # then
    assert set(mount) == {"vf-5194d5d8", "vf-70b99ea5", "vf-cd6c0b91", "vf-db50b713/subpath"}
    assert mount_map == {
        "vf-70b99ea5": "abcd",
        "vf-cd6c0b91": "qwer",
        "vf-db50b713/subpath": "/lorem/ipsum/dolor",
    }


def test_vfolder_mount_complex():
    # given
    mount = [
        "type=bind,source=/colon:path/test,target=/data",
        "type=bind,source=/usr/abcd,target=/home/work/zxcv,readonly",
        "type=bind,source=/usr/lorem,target=/home/work/ipsum,ro",
        "type=bind,source=/usr/dolor,target=/home/work/sit,rw",
    ]

    # when
    mount, mount_map, mount_options = prepare_mount_arg_v2(mount)

    # then
    assert set(mount) == {"/colon:path/test", "/usr/abcd", "/usr/lorem", "/usr/dolor"}
    assert mount_map == {
        "/colon:path/test": "/data",
        "/usr/abcd": "/home/work/zxcv",
        "/usr/lorem": "/home/work/ipsum",
        "/usr/dolor": "/home/work/sit",
    }
    assert mount_options == {
        "/colon:path/test": {
            "type": MountType.BIND,
            "readonly": False,
        },
        "/usr/abcd": {
            "type": MountType.BIND,
            "readonly": True,
        },
        "/usr/lorem": {
            "type": MountType.BIND,
            "readonly": True,
        },
        "/usr/dolor": {
            "type": MountType.BIND,
            "readonly": False,
        },
    }
