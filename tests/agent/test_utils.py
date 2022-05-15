import tempfile

import pytest

from ai.backend.agent import utils


def test_read_sysfs():
    with tempfile.NamedTemporaryFile('w') as f:
        f.write('10')
        f.flush()
        val = utils.read_sysfs(f.name, int)
        assert isinstance(val, int)
        assert val == 10
        val = utils.read_sysfs(f.name, str)
        assert isinstance(val, str)
        assert val == '10'
        val = utils.read_sysfs(f.name, float)
        assert isinstance(val, float)
        assert val == 10.0

    with tempfile.NamedTemporaryFile('w') as f:
        f.write('1')
        f.flush()
        val = utils.read_sysfs(f.name, bool)
        assert isinstance(val, bool)
        assert val is True
        f.seek(0, 0)
        f.write('0')
        f.flush()
        val = utils.read_sysfs(f.name, bool)
        assert isinstance(val, bool)
        assert val is False

    val = utils.read_sysfs('/tmp/xxxxx-non-existent-file', int)
    assert isinstance(val, int)
    assert val == 0

    val = utils.read_sysfs('/tmp/xxxxx-non-existent-file', int, -1)
    assert isinstance(val, int)
    assert val == -1

    with pytest.raises(TypeError):
        val = utils.read_sysfs('/tmp/xxxxx-non-existent-file', object)

    with pytest.raises(TypeError):
        val = utils.read_sysfs('/tmp/xxxxx-non-existent-file', object, -1)


def test_update_nested_dict():
    o = {
        'a': 1,
        'b': 2,
    }
    utils.update_nested_dict(o, {'a': 3, 'c': 4})
    assert o == {
        'a': 3,
        'b': 2,
        'c': 4,
    }

    o = {
        'a': {
            'x': 1,
        },
        'b': 2,
    }
    with pytest.raises(AssertionError):
        utils.update_nested_dict(o, {'a': 3})

    o = {
        'a': {
            'x': 1,
        },
        'b': 2,
    }
    utils.update_nested_dict(o, {'a': {'x': 3, 'y': 4}, 'b': 5})
    assert o['a'] == {
        'x': 3,
        'y': 4,
    }
    assert o['b'] == 5

    o = {
        'a': [1, 2],
        'b': 3,
    }
    utils.update_nested_dict(o, {'a': [4, 5], 'b': 6})
    assert o['a'] == [1, 2, 4, 5]
    assert o['b'] == 6
