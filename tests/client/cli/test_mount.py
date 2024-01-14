from ai.backend.cli.types import MountType
from ai.backend.client.cli.session.execute import prepare_mount_arg, prepare_mount_arg_v2


# docker/cli/cli/compose/loader/volume_test.go (https://github.com/docker/cli/blob/1fc6ef9d63d4442a56d0d5d551bb19c89bd35036/cli/compose/loader/volume_test.go#L107)  # noqa
def test_vfolder_mount_simple():
    # given
    mount = [
        "vf-5194d5d8",
        "vf-70b99ea5=abcd",
        "vf-cd6c0b91:qwer",
    ]

    # when
    mount, mount_map = prepare_mount_arg(mount)

    # then
    assert set(mount) == {"vf-5194d5d8", "vf-70b99ea5", "vf-cd6c0b91"}
    assert mount_map == {
        "vf-70b99ea5": "abcd",
        "vf-cd6c0b91": "qwer",
    }


def test_vfolder_mount_complex():
    # given
    mount = [
        "type=bind,source=/colon:path/test,target=/data",
        "type=bind,source=/usr/abcd,target=/home/work/zxcv,readonly",
    ]

    # when
    mount, mount_map, mount_options = prepare_mount_arg_v2(mount)

    # then
    assert set(mount) == {"/colon:path/test", "/usr/abcd"}
    assert mount_map == {
        "/colon:path/test": "/data",
        "/usr/abcd": "/home/work/zxcv",
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
    }
