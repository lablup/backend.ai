import json
from contextlib import closing

from ...utils.cli import EOF, ClientRunnerFunc, decode


def test_list_storage(run_admin: ClientRunnerFunc):
    """
    Test list storage.
    """
    print("[ List storage ]")
    with closing(run_admin(["--output=json", "admin", "storage", "list"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        storage_list = loaded.get("items")
        assert isinstance(storage_list, list), "Storage list not printed properly"


def test_info_storage(run_admin: ClientRunnerFunc):
    """
    Test storage info.
    """
    print("[ Print storage info ]")
    with closing(run_admin(["--output=json", "admin", "storage", "info", "local:volume1"])) as p:
        p.expect(EOF)
        decoded = decode(p.before)
        loaded = json.loads(decoded)
        storage_list = loaded.get("items")
        assert isinstance(storage_list, list), "Storage info not printed properly"
