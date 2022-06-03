import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc


def test_add_group(run: ClientRunnerFunc):
    pass


def test_update_group(run: ClientRunnerFunc):
    pass


def test_delete_group(run: ClientRunnerFunc):
    pass


def test_list_group(run: ClientRunnerFunc):
    print("[ List group ]")
    with closing(run(['--output=json', 'admin', 'group', 'list'])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        group_list = loaded.get('items')
        assert isinstance(group_list, list), 'Group list not printed properly'
