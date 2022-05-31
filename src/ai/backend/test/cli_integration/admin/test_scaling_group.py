import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc


def test_add_scaling_group(run: ClientRunnerFunc):
    # Create scaling group
    with closing(run([
        'admin', 'scaling-group', 'add',
        '-d', 'Test scaling group',
        '-i',
        '--driver', 'static',
        '--driver-opts', '{"x": 1}',
        '--scheduler', 'fifo',
        'test_group1',
    ])) as p:
        p.expect(EOF)
        assert 'Scaling group name test_group1 is created.' in p.before.decode(), \
            'Test scaling group not created successfully'

    # Check if scaling group is created
    with closing(run(['--output=json', 'admin', 'scaling-group', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        scaling_group_list = loaded.get('items')
        assert isinstance(scaling_group_list, list), 'Scaling group list not printed properly'

    test_group = get_scaling_group_from_list(scaling_group_list, 'test_group1')
    assert bool(test_group), 'Test scaling group doesn\'t exist'

    # Get the full detail.
    with closing(run(['--output=json', 'admin', 'scaling-group', 'info', 'test_group1'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        scaling_group_list = loaded.get('items')
        assert isinstance(scaling_group_list, list), 'Scaling group info not printed properly'

    test_group = get_scaling_group_from_list(scaling_group_list, 'test_group1')
    assert test_group.get('description') == 'Test scaling group', 'Scaling group description mismatch'
    assert test_group.get('is_active') is False, 'Scaling group active status mismatch'
    assert test_group.get('driver') == 'static', 'Scaling group driver mismatch'
    assert test_group.get('driver_opts') == {'x': 1}, 'Scaling group driver options mismatch'
    assert test_group.get('scheduler') == 'fifo', 'Scaling group scheduler mismatch'
    assert test_group.get('scheduler_opts') == {}, 'Scaling group scheduler options mismatch'


def test_update_scaling_group(run: ClientRunnerFunc):
    # Update scaling group
    with closing(run([
        'admin', 'scaling-group', 'update',
        '-d', 'Test scaling group updated',
        '--driver', 'non-static',
        '--scheduler', 'lifo',
        'test_group1',
    ])) as p:
        p.expect(EOF)
        assert 'Scaling group test_group1 is updated.' in p.before.decode(), \
            'Test scaling group not updated successfully'

    # Check if scaling group is updated
    with closing(run(['--output=json', 'admin', 'scaling-group', 'info', 'test_group1'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        scaling_group_list = loaded.get('items')
        assert isinstance(scaling_group_list, list), 'Scaling group list not printed properly'

    test_group = get_scaling_group_from_list(scaling_group_list, 'test_group1')

    assert bool(test_group), 'Test scaling group doesn\'t exist'
    assert test_group.get('description') == 'Test scaling group updated', 'Scaling group description mismatch'
    assert test_group.get('is_active') is True, 'Scaling group active status mismatch'
    assert test_group.get('driver') == 'non-static', 'Scaling group driver mismatch'
    assert test_group.get('driver_opts') == {'x': 1}, 'Scaling group driver options mismatch'
    assert test_group.get('scheduler') == 'lifo', 'Scaling group scheduler mismatch'
    assert test_group.get('scheduler_opts') == {}, 'Scaling group scheduler options mismatch'


def test_delete_scaling_group(run: ClientRunnerFunc):
    with closing(run(['admin', 'scaling-group', 'delete', 'test_group1'])) as p:
        p.expect(EOF)
        assert 'Scaling group is deleted: test_group1.' in p.before.decode(), 'Test scaling group deletion unsuccessful'


def test_list_scaling_group(run: ClientRunnerFunc):
    with closing(run(['--output=json', 'admin', 'scaling-group', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        scaling_group_list = loaded.get('items')
        assert isinstance(scaling_group_list, list), 'Scaling group list not printed properly'


def get_scaling_group_from_list(scaling_groups: list, groupname: str) -> dict:
    for sg in scaling_groups:
        if sg.get('name') == groupname:
            return sg
    return {}
