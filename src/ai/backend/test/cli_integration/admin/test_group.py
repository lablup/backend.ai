import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc


def test_add_group(run_admin: ClientRunnerFunc):
    pass


def test_update_group(run_admin: ClientRunnerFunc):
    pass


def test_delete_group(run_admin: ClientRunnerFunc):
    pass


def test_list_group(run_admin: ClientRunnerFunc):
    print("[ List group ]")
    with closing(run_admin(["--output=json", "admin", "group", "list"])) as p:
        p.expect(EOF)
        decoded = p.before.decode()
        loaded = json.loads(decoded)
        group_list = loaded.get("items")
        assert isinstance(group_list, list), "Group list not printed properly"
