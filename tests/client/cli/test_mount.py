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
            "readonly": None,
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


def test_vfolder_mount_v2_without_target():
    # given
    mount = [
        "type=volume,source=vf-dd244f7f,readonly",
    ]

    # when
    mount, mount_map, mount_options = prepare_mount_arg_v2(mount)

    # then
    assert set(mount) == {"vf-dd244f7f"}
    assert mount_map == {}
    assert mount_options == {
        "vf-dd244f7f": {
            "type": MountType.VOLUME,
            "readonly": True,
        },
    }


def test_vfolder_mount_simple_with_v2():
    # given
    mount = [
        "vf-d2340c9d",
        "vf-a3430d85:/home/work/v1",
        "vf-4bf23b66=/home/work/v1/tmp",
    ]

    # when
    mount_v1, mount_map_v1 = prepare_mount_arg(mount)
    mount_v2, mount_map_v2, mount_options_v2 = prepare_mount_arg_v2(mount)

    # then
    assert set(mount_v1) == set(mount_v2)
    assert mount_map_v1 == mount_map_v2
    assert mount_options_v2 == {
        "vf-d2340c9d": {
            "type": MountType.BIND,
            "readonly": None,
        },
        "vf-a3430d85": {
            "type": MountType.BIND,
            "readonly": None,
        },
        "vf-4bf23b66": {
            "type": MountType.BIND,
            "readonly": None,
        },
    }
