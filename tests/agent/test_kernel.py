import pytest

from ai.backend.agent.kernel import (
    match_distro_data,
)


def test_match_distro_data():
    krunner_volumes = {
        'ubuntu8.04': 'u1',
        'ubuntu18.04': 'u2',
        'centos7.6': 'c1',
        'centos8.0': 'c2',
        'centos5.0': 'c3',
    }

    ret = match_distro_data(krunner_volumes, 'centos7.6')
    assert ret[0] == 'centos7.6'
    assert ret[1] == 'c1'

    ret = match_distro_data(krunner_volumes, 'centos8.0')
    assert ret[0] == 'centos8.0'
    assert ret[1] == 'c2'

    ret = match_distro_data(krunner_volumes, 'centos')
    assert ret[0] == 'centos8.0'  # assume latest
    assert ret[1] == 'c2'

    ret = match_distro_data(krunner_volumes, 'ubuntu18.04')
    assert ret[0] == 'ubuntu18.04'
    assert ret[1] == 'u2'

    ret = match_distro_data(krunner_volumes, 'ubuntu20.04')
    assert ret[0] == 'ubuntu18.04'
    assert ret[1] == 'u2'

    ret = match_distro_data(krunner_volumes, 'ubuntu')
    assert ret[0] == 'ubuntu18.04'  # assume latest
    assert ret[1] == 'u2'

    with pytest.raises(RuntimeError):
        match_distro_data(krunner_volumes, 'ubnt')

    with pytest.raises(RuntimeError):
        match_distro_data(krunner_volumes, 'xyz')


def test_match_distro_data_with_libc_based_krunners():
    krunner_volumes = {
        'static-gnu': 'x1',
        'static-musl': 'x2',
    }

    # when there are static builds, it returns the distro name as-is
    # and only distinguish the libc flavor (gnu or musl).

    ret = match_distro_data(krunner_volumes, 'centos7.6')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'centos8.0')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'centos')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'ubuntu18.04')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'ubuntu')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'alpine3.8')
    assert ret[0] == 'static-musl'
    assert ret[1] == 'x2'

    ret = match_distro_data(krunner_volumes, 'alpine')
    assert ret[0] == 'static-musl'
    assert ret[1] == 'x2'

    ret = match_distro_data(krunner_volumes, 'alpine3.11')
    assert ret[0] == 'static-musl'
    assert ret[1] == 'x2'

    # static-gnu works as a generic fallback in all unknown distributions
    ret = match_distro_data(krunner_volumes, 'ubnt')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'xyz')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'


def test_match_distro_data_with_libc_based_krunners_mixed():
    krunner_volumes = {
        'static-gnu': 'x1',
        'alpine3.8': 'c1',
        'alpine3.11': 'c2',
    }

    ret = match_distro_data(krunner_volumes, 'centos7.6')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'centos8.0')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'centos')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'ubuntu18.04')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'ubuntu')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'alpine3.8')
    assert ret[0] == 'alpine3.8'
    assert ret[1] == 'c1'

    ret = match_distro_data(krunner_volumes, 'alpine')
    assert ret[0] == 'alpine3.11'  # assume latest
    assert ret[1] == 'c2'

    ret = match_distro_data(krunner_volumes, 'alpine3.11')
    assert ret[0] == 'alpine3.11'
    assert ret[1] == 'c2'

    # static-gnu works as a generic fallback in all unknown distributions
    ret = match_distro_data(krunner_volumes, 'ubnt')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'

    ret = match_distro_data(krunner_volumes, 'xyz')
    assert ret[0] == 'static-gnu'
    assert ret[1] == 'x1'
