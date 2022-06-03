import pickle

import toml
from toml.decoder import InlineTableDict

from ai.backend.common.config import override_key, merge, _sanitize_inline_dicts


def test_override_key():
    sample = {
        'a': {
            'b': 0,
        },
        'c': 1,
    }
    override_key(sample, ('a', 'b'), -1)
    assert sample['a']['b'] == -1
    assert sample['c'] == 1

    sample = {
        'a': {
            'b': 0,
        },
        'c': 1,
    }
    override_key(sample, ('c',), -1)
    assert sample['a']['b'] == 0
    assert sample['c'] == -1


def test_merge():
    left = {
        'a': {
            'a': 5,
            'b': 0,
        },
        'c': 1,
    }
    right = {
        'a': {
            'b': 2,
            'c': 3,
        },
        'x': 10,
    }
    result = merge(left, right)
    assert result == {
        'a': {
            'a': 5,
            'b': 2,
            'c': 3,
        },
        'c': 1,
        'x': 10,
    }


def test_sanitize_inline_dicts():
    sample = '''
    [section]
    a = { x = 1, y = 1 }
    b = { x = 1, y = { t = 2, u = 2 } }
    '''

    result = toml.loads(sample)
    assert isinstance(result['section']['a'], dict)
    assert isinstance(result['section']['a'], InlineTableDict)
    assert isinstance(result['section']['b'], dict)
    assert isinstance(result['section']['b'], InlineTableDict)
    assert isinstance(result['section']['b']['y'], dict)
    assert isinstance(result['section']['b']['y'], InlineTableDict)

    result = _sanitize_inline_dicts(result)
    assert isinstance(result['section']['a'], dict)
    assert not isinstance(result['section']['a'], InlineTableDict)
    assert isinstance(result['section']['b'], dict)
    assert not isinstance(result['section']['b'], InlineTableDict)
    assert isinstance(result['section']['b']['y'], dict)
    assert not isinstance(result['section']['b']['y'], InlineTableDict)

    # Also ensure the result is picklable.
    data = pickle.dumps(result)
    result = pickle.loads(data)
    assert result == {
        'section': {
            'a': {'x': 1, 'y': 1},
            'b': {'x': 1, 'y': {'t': 2, 'u': 2}},
        },
    }
